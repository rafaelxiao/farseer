"""
baostock data source fetcher.

Stores 后复权 (backward-adjusted) prices with backward_factor.

后复权:
- Historical prices are actual (immutable)
- Recent prices adjusted UP for splits/dividends
- backward_factor = cumulative from IPO (monotonically increasing)

Conversion:
- 前复权 (forward) = 后复权 / backward_factor * latest_backward_factor
- Actual price = 后复权 / backward_factor
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase
from farseer.symbols.converter import SymbolConverter


TIMEFRAME_MAP = {
    "1d": "d",
    "1w": "w",
    "1M": "m",
}

_executor = ThreadPoolExecutor(max_workers=2)


class BaostockFetcher(BaseFetcher):
    """Fetch data from baostock (free Chinese A-share data)."""

    name = "baostock"
    supported_exchanges = ["SH", "SZ"]

    def _fetch_sync(
        self,
        symbol: str,
        timeframe: str,
        start: str | None,
        end: str | None,
    ) -> list[dict]:
        """Sync fetch from baostock (runs in thread)."""
        import baostock as bs

        bs_symbol = SymbolConverter.to_baostock(symbol)
        frequency = TIMEFRAME_MAP.get(timeframe, "d")

        # Fetch from start (or IPO) to get proper backward_factor
        start_date = start[:10] if start else "1990-01-01"
        end_date = end[:10] if end else datetime.now().strftime("%Y-%m-%d")
        fields = "date,open,high,low,close,volume,amount"

        rs = bs.login()
        if rs.error_code != '0':
            raise Exception(f"baostock login failed: {rs.error_msg}")

        try:
            # Fetch 后复权 (backward-adjusted, flag=2)
            rs_backward = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="2",
            )
            backward_rows = []
            while rs_backward.next():
                backward_rows.append(rs_backward.get_row_data())

            # Fetch 前复权 (forward-adjusted, flag=3)
            rs_forward = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="3",
            )
            forward_rows = []
            while rs_forward.next():
                forward_rows.append(rs_forward.get_row_data())

            if not backward_rows or not forward_rows:
                return []

            # Calculate CUMULATIVE backward_factor
            # 
            # Convention:
            # - backward_factor starts at 1.0 (IPO)
            # - Increases with each split/dividend
            # - forward = backward / backward_factor * latest_backward_factor
            #
            # Formula: backward_factor = (backward / forward) normalized to start at 1.0
            
            # First, calculate raw ratios (backward / forward)
            raw_ratios = []
            for bwd, fwd in zip(backward_rows, forward_rows):
                bwd_close = float(bwd[4]) if bwd[4] else 0
                fwd_close = float(fwd[4]) if fwd[4] else 0
                # Use backward/forward ratio (increases over time)
                ratio = (bwd_close / fwd_close) if fwd_close > 0 else 1.0
                raw_ratios.append(ratio)
            
            # Normalize so first date = 1.0
            first_ratio = raw_ratios[0] if raw_ratios[0] > 0 else 1.0
            cumulative_factors = [r / first_ratio for r in raw_ratios]
            
            records = []
            for i, (bwd, fwd) in enumerate(zip(backward_rows, forward_rows)):
                records.append({
                    "date": bwd[0],
                    "open": float(bwd[1]) if bwd[1] else 0,  # 后复权
                    "high": float(bwd[2]) if bwd[2] else 0,
                    "low": float(bwd[3]) if bwd[3] else 0,
                    "close": float(bwd[4]) if bwd[4] else 0,
                    "volume": int(float(bwd[5])) if bwd[5] else 0,
                    "amount": float(bwd[6]) if bwd[6] else 0,
                    "backward_factor": round(cumulative_factors[i], 10),
                })

            return records

        finally:
            bs.logout()

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from baostock (async wrapper)."""

        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        records = []
        for row in raw_records:
            record = OHLCBase(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                backward_factor=row["backward_factor"],
                data={"amount": row["amount"], "source": "baostock"},
            )
            records.append(record)

        return records


FetcherRegistry.register(BaostockFetcher())
