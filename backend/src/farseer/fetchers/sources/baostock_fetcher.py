"""
Baostock data source fetcher for Chinese A-shares.

Adjustment:
- Stocks: Uses query_adjust_factor() → backAdjustFactor for proper adjustment
- ETFs: No adjustment API available → backward_factor = 1.0
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase


_executor = ThreadPoolExecutor(max_workers=2)

TIMEFRAME_MAP = {"1d": "d", "1w": "w", "1M": "m"}


def _to_baostock_symbol(symbol: str) -> str:
    """Farseer → Baostock: 600519.SH → sh.600519"""
    if "." not in symbol:
        raise ValueError(f"Invalid symbol: {symbol}")
    code, exchange = symbol.split(".", 1)
    return f"{'sh' if exchange == 'SH' else 'sz'}.{code}"


class BaostockFetcher(BaseFetcher):
    name = "baostock"
    supported_exchanges = ["SH", "SZ"]

    def _fetch_adjust_factors(self, bs_symbol: str, start: str, end: str) -> dict[str, float]:
        """Get adjustment factors by date using query_adjust_factor."""
        import baostock as bs
        factors = {}
        try:
            rs = bs.query_adjust_factor(bs_symbol, start, end)
            while rs.next():
                row = rs.get_row_data()
                trade_date = row[1]  # dividOperateDate
                back_factor = float(row[3])  # backAdjustFactor
                factors[trade_date] = back_factor
        except Exception:
            pass
        return factors

    def _fetch_sync(
        self, symbol: str, timeframe: str = "1d",
        start: str | None = None, end: str | None = None,
    ) -> list[dict]:
        import baostock as bs
        from farseer.symbols.utils import is_etf

        bs_symbol = _to_baostock_symbol(symbol)
        frequency = TIMEFRAME_MAP.get(timeframe, "d")
        start_date = start[:10] if start else "1990-01-01"
        end_date = end[:10] if end else datetime.now().strftime("%Y-%m-%d")

        rs = bs.login()
        if rs.error_code != '0':
            raise Exception(f"Baostock login failed: {rs.error_msg}")

        try:
            # Fetch OHLC (flag=2 = 后复权/raw prices)
            rs_ohlc = bs.query_history_k_data_plus(
                bs_symbol, "date,open,high,low,close,volume,amount",
                start_date, end_date, frequency, adjustflag="2",
            )
            rows = []
            while rs_ohlc.next():
                rows.append(rs_ohlc.get_row_data())

            if not rows:
                return []

            # Get adjustment factors (query from 1990 to catch all events before start_date)
            if is_etf(symbol):
                adjust_map = {}
            else:
                adjust_map = self._fetch_adjust_factors(bs_symbol, "1990-01-01", end_date)

            # Build cumulative factor map: factor carries forward to all later dates
            sorted_factors = sorted(adjust_map.items())  # [(date, factor), ...]
            
            # Process records with correct factor for each date
            records = []
            factor_idx = 0
            current_factor = 1.0
            
            for row in rows:
                date = row[0]
                raw_open = float(row[1]) if row[1] else 0
                raw_high = float(row[2]) if row[2] else 0
                raw_low = float(row[3]) if row[3] else 0
                raw_close = float(row[4]) if row[4] else 0

                # Advance factor to latest <= this date
                while factor_idx < len(sorted_factors) and sorted_factors[factor_idx][0] <= date:
                    current_factor = sorted_factors[factor_idx][1]
                    factor_idx += 1

                bf = current_factor

                # Store 后复权 = raw × cumulative backAdjustFactor
                records.append({
                    "date": date,
                    "open": raw_open * bf,
                    "high": raw_high * bf,
                    "low": raw_low * bf,
                    "close": raw_close * bf,
                    "volume": int(float(row[5])) if row[5] else 0,
                    "amount": float(row[6]) if row[6] else 0,
                    "backward_factor": round(bf, 10),
                })

            return records

        finally:
            bs.logout()

    async def _fetch_ohlc(
        self, symbol: str, timeframe: str = "1d",
        start: str | None = None, end: str | None = None,
    ) -> list[OHLCBase]:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        return [
            OHLCBase(
                symbol=symbol,
                data_source="baostock",
                timeframe=timeframe,
                timestamp=datetime.strptime(r["date"], "%Y-%m-%d"),
                open=r["open"], high=r["high"], low=r["low"], close=r["close"],
                volume=r["volume"], backward_factor=r["backward_factor"],
                data={"amount": r["amount"], "source": "baostock"},
            )
            for r in raw
        ]


FetcherRegistry.register(BaostockFetcher())
