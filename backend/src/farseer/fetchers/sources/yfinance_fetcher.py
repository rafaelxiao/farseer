"""
yfinance data source fetcher.

Symbol format: 600519.SH -> 600519.SS (yfinance uses .SS for Shanghai)

Adjustment:
- yfinance provides 'Adj Close' column
- adjustor_factor = Adj Close / Close
- When auto_adjust=True (default), yfinance returns adjusted OHLC directly
- We use auto_adjust=False to get both original and adjusted values
"""

from datetime import datetime

import yfinance as yf

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase
from farseer.symbols.converter import SymbolConverter


# Map our timeframe to yfinance interval
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


class YFinanceFetcher(BaseFetcher):
    """Fetch data from Yahoo Finance via yfinance."""

    name = "yfinance"
    supported_exchanges = ["SH", "SZ", "HK", "US"]

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from yfinance."""

        # Convert symbol: 600519.SH -> 600519.SS
        yf_symbol = SymbolConverter.to_yfinance(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1d")

        # yfinance date format
        start_date = start[:10] if start else None
        end_date = end[:10] if end else None

        # Fetch with auto_adjust=False to get Adj Close
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,  # Get original + adjusted
        )

        if hist.empty:
            return []

        records = []
        for idx, row in hist.iterrows():
            # Calculate adjustor factor
            close = row["Close"]
            adj_close = row.get("Adj Close", close)
            adjustor_factor = (adj_close / close) if close != 0 else 1.0

            # Extra data
            extra = {}
            if "Stock Splits" in row and row["Stock Splits"] > 0:
                extra["stock_splits"] = float(row["Stock Splits"])
            if "Dividends" in row and row["Dividends"] > 0:
                extra["dividends"] = float(row["Dividends"])

            record = OHLCBase(
                symbol=symbol,  # Use Farseer canonical symbol
                timeframe=timeframe,
                timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.fromisoformat(str(idx)),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(close),
                volume=int(row.get("Volume", 0)),
                adjustor_factor=round(adjustor_factor, 8),
                data=extra,
            )
            records.append(record)

        return records


# Auto-register
FetcherRegistry.register(YFinanceFetcher())
