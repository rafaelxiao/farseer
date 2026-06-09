"""
yfinance data source fetcher.

Stores TRUE backward factors (后复权):
- Historical: backward_factor = 1.0 (prices stay actual)
- Recent: backward_factor > 1.0 (prices adjusted UP)
- When new split: historical data UNCHANGED ✓

Formula: backward_factor = forward_factor / forward_factor_first
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
        """Fetch OHLC with TRUE backward factors."""

        yf_symbol = SymbolConverter.to_yfinance(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1d")
        start_date = start[:10] if start else None
        end_date = end[:10] if end else None

        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,
        )

        if hist.empty:
            return []

        # First pass: get forward_factors
        forward_factors = []
        rows_data = []
        for idx, row in hist.iterrows():
            close = row["Close"]
            adj_close = row.get("Adj Close", close)
            forward_factor = (adj_close / close) if close != 0 else 1.0
            forward_factors.append(forward_factor)

            extra = {}
            if "Stock Splits" in row and row["Stock Splits"] > 0:
                extra["stock_splits"] = float(row["Stock Splits"])
            if "Dividends" in row and row["Dividends"] > 0:
                extra["dividends"] = float(row["Dividends"])

            rows_data.append({
                "timestamp": idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.fromisoformat(str(idx)),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(close),
                "volume": int(row.get("Volume", 0)),
                "forward_factor": forward_factor,
                "extra": extra,
            })

        # Calculate backward factors
        # backward_factor = forward_factor / forward_factor_first
        # This ensures:
        #   - First date: backward_factor = 1.0 (historical prices stay actual)
        #   - Later dates: backward_factor >= 1.0 (prices adjusted UP)
        first_forward = forward_factors[0] if forward_factors else 1.0

        records = []
        for data in rows_data:
            backward_factor = data["forward_factor"] / first_forward if first_forward else 1.0

            record = OHLCBase(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=data["timestamp"],
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                volume=data["volume"],
                backward_factor=round(backward_factor, 10),
                data=data["extra"],
            )
            records.append(record)

        return records


FetcherRegistry.register(YFinanceFetcher())
