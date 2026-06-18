"""
Yahoo Finance data source fetcher.

Supports:
- Global stocks (US, HK, etc.)
- ETFs and funds
- OHLC data with adjustment factors

Symbol format: AAPL, 0700.HK, 600519.SS
Farseer format: AAPL.US, 0700.HK, 600519.SH
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase


_executor = ThreadPoolExecutor(max_workers=2)

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "1d": "1d",
    "1w": "1wk",
    "1M": "1mo",
}


def _to_yfinance_symbol(symbol: str) -> str:
    """Convert Farseer symbol to Yahoo Finance format."""
    if "." not in symbol:
        return symbol  # US stocks like AAPL
    
    code, exchange = symbol.split(".", 1)
    
    if exchange == "SH":
        return f"{code}.SS"
    elif exchange == "SZ":
        return f"{code}.SZ"
    elif exchange == "HK":
        return f"{code}.HK"
    else:
        return symbol


class YFinanceFetcher(BaseFetcher):
    """Fetch data from Yahoo Finance."""

    name = "yfinance"
    supported_exchanges = ["US", "HK", "SH", "SZ"]

    def _fetch_sync(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        """Sync fetch from Yahoo Finance."""
        import yfinance as yf

        yf_symbol = _to_yfinance_symbol(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1d")

        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=start[:10] if start else None,
            end=end[:10] if end else None,
            interval=interval,
            auto_adjust=False,
        )

        if hist.empty:
            return []

        records = []
        for idx, row in hist.iterrows():
            close = row["Close"]
            adj_close = row.get("Adj Close", close)
            forward_factor = (adj_close / close) if close != 0 else 1.0

            extra = {}
            if "Stock Splits" in row and row["Stock Splits"] > 0:
                extra["stock_splits"] = float(row["Stock Splits"])
            if "Dividends" in row and row["Dividends"] > 0:
                extra["dividends"] = float(row["Dividends"])

            records.append({
                "date": str(idx.date()) if hasattr(idx, 'date') else str(idx)[:10],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(close),
                "volume": int(row.get("Volume", 0)),
                "forward_factor": forward_factor,
                "extra": extra,
            })

        return records

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from Yahoo Finance (async wrapper)."""

        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        if not raw_records:
            return []

        # Calculate backward factors
        first_forward = raw_records[0]["forward_factor"]

        records = []
        for row in raw_records:
            backward_factor = row["forward_factor"] / first_forward if first_forward else 1.0

            record = OHLCBase(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                backward_factor=round(backward_factor, 10),
                data={**row["extra"], "source": "yfinance"},
            )
            records.append(record)

        return records


FetcherRegistry.register(YFinanceFetcher())
