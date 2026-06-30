"""
Binance data source fetcher for cryptocurrency.

Supports:
- OHLC data for all trading pairs
- Market data (volume, market cap)

Symbol format: BTCUSDT, ETHUSDT (no separator)
Farseer format: BTC.USDT, ETH.USDT
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.sources.base import BaseFetcher
from farseer.sources.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase


_executor = ThreadPoolExecutor(max_workers=2)

# Binance API base
BINANCE_API = "https://api.binance.com"

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1w": "1w",
}


def _parse_symbol(symbol: str) -> tuple[str, str]:
    """Parse Farseer symbol to Binance format: BTC.USDT -> (BTC, USDT)."""
    if "." in symbol:
        base, quote = symbol.split(".", 1)
        return base, quote
    # Assume USDT if no quote specified
    return symbol, "USDT"


class BinanceFetcher(BaseFetcher):
    """Fetch crypto data from Binance."""

    name = "binance"
    supported_exchanges = ["CRYPTO"]

    def _fetch_sync(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        """Sync fetch from Binance API."""
        import requests

        base, quote = _parse_symbol(symbol)
        trading_pair = f"{base}{quote}".upper()
        interval = TIMEFRAME_MAP.get(timeframe, "1d")

        # Calculate timestamps
        if start:
            start_ts = int(datetime.strptime(start[:10], "%Y-%m-%d").timestamp() * 1000)
        else:
            # Default: 1 year of data
            start_ts = int((datetime.now().timestamp() - 365 * 24 * 3600) * 1000)

        if end:
            end_ts = int(datetime.strptime(end[:10], "%Y-%m-%d").timestamp() * 1000)
        else:
            end_ts = int(datetime.now().timestamp() * 1000)

        # Fetch klines
        url = f"{BINANCE_API}/api/v3/klines"
        params = {
            "symbol": trading_pair,
            "interval": interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": 1000,
        }

        all_records = []
        while start_ts < end_ts:
            params["startTime"] = start_ts
            params["endTime"] = end_ts

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for kline in data:
                # [open_time, open, high, low, close, volume, close_time, ...]
                all_records.append({
                    "date": datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "amount": float(kline[7]),  # Quote asset volume
                })

            # Move to next batch
            start_ts = data[-1][6] + 1  # close_time + 1ms
            time.sleep(0.1)  # Rate limit

        return all_records

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from Binance (async wrapper)."""

        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        records = []
        for row in raw_records:
            record = OHLCBase(
                symbol=symbol,
                data_source="binance",
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=int(row["volume"]),
                backward_factor=1.0,  # Crypto doesn't have splits/dividends
                data={"amount": row["amount"], "source": "binance"},
            )
            records.append(record)

        return records


FetcherRegistry.register(BinanceFetcher())
