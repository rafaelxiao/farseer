"""
baostock data source fetcher.

Fetches FULL history from IPO to get correct backward_factors.
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

        # Always fetch from IPO to get correct backward_factors
        start_date = "1990-01-01"  # Before any A-share existed
        end_date = end[:10] if end else datetime.now().strftime("%Y-%m-%d")
        fields = "date,open,high,low,close,volume,amount"

        rs = bs.login()
        if rs.error_code != '0':
            raise Exception(f"baostock login failed: {rs.error_msg}")

        try:
            # Fetch raw prices (不复权) - for calculating factors
            rs_raw = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="1",
            )
            raw_rows = []
            while rs_raw.next():
                raw_rows.append(rs_raw.get_row_data())

            # Fetch forward-adjusted prices (前复权)
            rs_fwd = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="3",
            )
            fwd_rows = []
            while rs_fwd.next():
                fwd_rows.append(rs_fwd.get_row_data())

            if not raw_rows or not fwd_rows:
                return []

            # Calculate backward_factors
            # backward_factor = forward_factor / forward_factor_first
            # Where forward_factor = fwd_close / raw_close
            first_raw_close = float(raw_rows[0][4]) if raw_rows[0][4] else 1.0
            first_fwd_close = float(fwd_rows[0][4]) if fwd_rows[0][4] else 1.0
            first_forward_factor = first_fwd_close / first_raw_close if first_raw_close else 1.0

            records = []
            for raw, fwd in zip(raw_rows, fwd_rows):
                raw_close = float(raw[4]) if raw[4] else 0
                fwd_close = float(fwd[4]) if fwd[4] else 0

                # Current forward factor
                forward_factor = fwd_close / raw_close if raw_close > 0 else 1.0

                # Backward factor: normalized so first date = 1.0
                backward_factor = forward_factor / first_forward_factor if first_forward_factor else 1.0

                records.append({
                    "date": fwd[0],
                    "open": float(fwd[1]) if fwd[1] else 0,
                    "high": float(fwd[2]) if fwd[2] else 0,
                    "low": float(fwd[3]) if fwd[3] else 0,
                    "close": fwd_close,
                    "volume": int(float(fwd[5])) if fwd[5] else 0,
                    "amount": float(fwd[6]) if fwd[6] else 0,
                    "backward_factor": round(backward_factor, 10),
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
                data={"amount": row["amount"]},
            )
            records.append(record)

        return records


FetcherRegistry.register(BaostockFetcher())
