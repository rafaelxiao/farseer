"""
baostock data source fetcher.

Symbol format: 600519.SH -> sh.600519 (baostock uses sh./sz. prefix)

Adjustment:
- adjustflag=1 (不复权): Cumulative value, NOT actual prices - DO NOT USE
- adjustflag=2 (后复权): Backward adjusted
- adjustflag=3 (前复权): Forward adjusted

Problem: baostock doesn't provide actual trading prices directly.
Solution: Fetch forward-adjusted prices, calculate factor to get actual.

For recent data: forward_adjusted ≈ actual price
For historical: actual = forward_adjusted / cumulative_factor

We fetch both (flag=1 and flag=3) to calculate the real adjustment factor.
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
        start_date = start[:10] if start else "1990-01-01"
        end_date = end[:10] if end else datetime.now().strftime("%Y-%m-%d")
        fields = "date,open,high,low,close,volume,amount"

        rs = bs.login()
        if rs.error_code != '0':
            raise Exception(f"baostock login failed: {rs.error_msg}")

        try:
            # Fetch raw (cumulative) prices
            rs_raw = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="1",
            )
            raw_rows = []
            while rs_raw.next():
                raw_rows.append(rs_raw.get_row_data())

            # Fetch forward-adjusted prices (matches real market for recent)
            rs_fwd = bs.query_history_k_data_plus(
                bs_symbol, fields, start_date, end_date, frequency, adjustflag="3",
            )
            fwd_rows = []
            while rs_fwd.next():
                fwd_rows.append(rs_fwd.get_row_data())

            # Combine: actual = forward_adjusted, factor = forward / raw
            records = []
            for raw, fwd in zip(raw_rows, fwd_rows):
                raw_close = float(raw[4]) if raw[4] else 0
                fwd_close = float(fwd[4]) if fwd[4] else 0
                
                # Adjustment factor: how much forward differs from raw
                # This factor lets us convert: actual_price = raw_price * factor
                factor = (fwd_close / raw_close) if raw_close > 0 else 1.0

                records.append({
                    "date": fwd[0],
                    "open": float(fwd[1]) if fwd[1] else 0,   # Forward adjusted (≈actual for recent)
                    "high": float(fwd[2]) if fwd[2] else 0,
                    "low": float(fwd[3]) if fwd[3] else 0,
                    "close": fwd_close,
                    "volume": int(float(fwd[5])) if fwd[5] else 0,
                    "amount": float(fwd[6]) if fwd[6] else 0,
                    "adjustor_factor": round(factor, 8),
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
                adjustor_factor=row["adjustor_factor"],
                data={"amount": row["amount"]},
            )
            records.append(record)

        return records


FetcherRegistry.register(BaostockFetcher())
