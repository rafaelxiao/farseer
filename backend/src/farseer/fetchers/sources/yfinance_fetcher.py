"""
yfinance data source fetcher.

Symbol format: 600519.SH -> 600519.SS (yfinance uses .SS for Shanghai)

Adjustment:
- auto_adjust=False: Returns original prices + Adj Close
- adjustor_factor = Adj Close / Close
- Stores ACTUAL trading prices, factor tells you how to adjust
"""

from datetime import datetime

import yfinance as yf

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase
from farseer.symbols.converter import SymbolConverter


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

        yf_symbol = SymbolConverter.to_yfinance(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1d")
        start_date = start[:10] if start else None
        end_date = end[:10] if end else None

        # auto_adjust=False: get original prices + Adj Close
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,  # Get actual prices + adjusted
        )

        if hist.empty:
            return []

        records = []
        for idx, row in hist.iterrows():
            # ACTUAL trading prices (not adjusted)
            close = row["Close"]
            adj_close = row.get("Adj Close", close)
            
            # Factor = adjusted / actual
            # For recent: factor ≈ 1.0
            # For historical (after splits): factor < 1.0
            adjustor_factor = (adj_close / close) if close != 0 else 1.0

            # Extra data
            extra = {}
            if "Stock Splits" in row and row["Stock Splits"] > 0:
                extra["stock_splits"] = float(row["Stock Splits"])
            if "Dividends" in row and row["Dividends"] > 0:
                extra["dividends"] = float(row["Dividends"])

            record = OHLCBase(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.fromisoformat(str(idx)),
                open=float(row["Open"]),       # Actual price
                high=float(row["High"]),       # Actual price
                low=float(row["Low"]),         # Actual price
                close=float(close),            # Actual price
                volume=int(row.get("Volume", 0)),
                adjustor_factor=round(adjustor_factor, 8),
                data=extra,
            )
            records.append(record)

        return records


FetcherRegistry.register(YFinanceFetcher())
