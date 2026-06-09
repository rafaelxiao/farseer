"""
baostock data source fetcher.

Symbol format: 600519.SH -> sh.600519 (baostock uses sh./sz. prefix)

Note: baostock is sync, so we run in executor.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase
from farseer.symbols.converter import SymbolConverter


# baostock frequency mapping
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

        # Convert: 600519.SH -> sh.600519
        bs_symbol = SymbolConverter.to_baostock(symbol)
        frequency = TIMEFRAME_MAP.get(timeframe, "d")

        # Default dates
        start_date = start[:10] if start else "2020-01-01"
        end_date = end[:10] if end else datetime.now().strftime("%Y-%m-%d")

        # Fields to fetch
        fields = "date,open,high,low,close,volume,amount,adjustflag"

        rs = bs.login()
        if rs.error_code != '0':
            raise Exception(f"baostock login failed: {rs.error_msg}")

        try:
            result = bs.query_history_k_data_plus(
                bs_symbol,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag="3",  # 3 = forward adjusted
            )

            records = []
            while result.next():
                row = result.get_row_data()
                records.append({
                    "date": row[0],
                    "open": float(row[1]) if row[1] else 0,
                    "high": float(row[2]) if row[2] else 0,
                    "low": float(row[3]) if row[3] else 0,
                    "close": float(row[4]) if row[4] else 0,
                    "volume": int(float(row[5])) if row[5] else 0,
                    "amount": float(row[6]) if row[6] else 0,
                    "adjustflag": row[7],
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

        # Run sync code in thread
        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor,
            self._fetch_sync,
            symbol,
            timeframe,
            start,
            end,
        )

        # Convert to OHLCBase
        records = []
        for row in raw_records:
            # baostock provides forward-adjusted prices
            # We use adjustor_factor=1.0 since data is already adjusted
            # For raw data, use adjustflag="1" and calculate factor

            record = OHLCBase(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                adjustor_factor=1.0,  # Already adjusted
                data={"amount": row["amount"]},
            )
            records.append(record)

        return records


# Auto-register
FetcherRegistry.register(BaostockFetcher())
