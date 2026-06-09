"""
yfinance data source fetcher.

Stores:
- Actual trading prices (Close, not adjusted)
- backward_factor for adjustment calculations

Conversion:
- backward_factor = forward_factor * latest_backward_factor
- Where forward_factor = Adj Close / Close
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
        """Fetch OHLC from yfinance with backward_factor."""

        yf_symbol = SymbolConverter.to_yfinance(symbol)
        interval = TIMEFRAME_MAP.get(timeframe, "1d")
        start_date = start[:10] if start else None
        end_date = end[:10] if end else None

        # auto_adjust=False: get actual prices + Adj Close
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=False,
        )

        if hist.empty:
            return []

        # First pass: calculate forward_factors
        rows_data = []
        for idx, row in hist.iterrows():
            close = row["Close"]
            adj_close = row.get("Adj Close", close)
            forward_factor = (adj_close / close) if close != 0 else 1.0

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
                "forward_factor": round(forward_factor, 10),
                "extra": extra,
            })

        # Calculate backward_factors
        # backward_factor = forward_factor / latest_forward_factor
        # This normalizes so latest backward_factor ≈ 1.0
        latest_forward = rows_data[-1]["forward_factor"] if rows_data else 1.0

        records = []
        for data in rows_data:
            backward_factor = data["forward_factor"] / latest_forward if latest_forward else 1.0

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
