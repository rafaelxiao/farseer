"""
AKShare data source fetcher.

Supports:
- A-share stocks (SH, SZ)
- ETFs
- OHLC data with adjustment factors

Symbol format: Same as Farseer (600519.SH, 159915.SZ)

Adjustment:
- Fetches both raw (不复权) and 后复权 prices
- Calculates backward_factor = hfq_close / raw_close
- Normalizes so first date = 1.0
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.sources.base import BaseFetcher
from farseer.sources.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase


_executor = ThreadPoolExecutor(max_workers=2)


def _to_akshare_symbol(symbol: str) -> str:
    """Convert Farseer symbol to AKShare format: 600519.SH -> 600519"""
    if "." in symbol:
        code, _ = symbol.split(".", 1)
        return code
    return symbol


class AKShareFetcher(BaseFetcher):
    """Fetch data from AKShare."""

    name = "akshare"
    supported_exchanges = ["SH", "SZ"]

    def _fetch_sync(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[dict]:
        """Sync fetch from AKShare."""
        import akshare as ak

        ak_symbol = _to_akshare_symbol(symbol)
        
        start_date = start[:10].replace("-", "") if start else "19900101"
        end_date = end[:10].replace("-", "") if end else datetime.now().strftime("%Y%m%d")

        try:
            # Fetch raw prices (不复权)
            df_raw = ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="",  # 不复权
            )

            if df_raw is None or len(df_raw) == 0:
                return []

            # Fetch 后复权 prices
            df_hfq = ak.stock_zh_a_hist(
                symbol=ak_symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="hfq",
            )

            if df_hfq is None or len(df_hfq) == 0:
                return []

            # Align by date
            raw_map = {}
            for _, row in df_raw.iterrows():
                date_str = str(row["日期"])
                raw_map[date_str] = float(row["收盘"])

            hfq_map = {}
            for _, row in df_hfq.iterrows():
                date_str = str(row["日期"])
                hfq_map[date_str] = {
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": float(row["成交额"]),
                }

            # Calculate backward_factor
            records = []
            dates = sorted(raw_map.keys())
            
            if not dates:
                return []

            # Find first valid date for normalization
            first_factor = None
            for date in dates:
                if date in hfq_map and raw_map.get(date, 0) > 0:
                    first_factor = hfq_map[date]["close"] / raw_map[date]
                    break

            if first_factor is None or first_factor == 0:
                first_factor = 1.0

            for date in dates:
                if date not in hfq_map:
                    continue
                
                raw_close = raw_map.get(date, 0)
                hfq_data = hfq_map[date]
                
                # backward_factor = hfq_close / raw_close, normalized
                if raw_close > 0:
                    factor = hfq_data["close"] / raw_close / first_factor
                else:
                    factor = 1.0

                records.append({
                    "date": date,
                    "open": hfq_data["open"],
                    "high": hfq_data["high"],
                    "low": hfq_data["low"],
                    "close": hfq_data["close"],  # Store 后复权 prices
                    "volume": hfq_data["volume"],
                    "amount": hfq_data["amount"],
                    "backward_factor": round(factor, 10),
                })

            return records

        except Exception as e:
            raise Exception(f"AKShare fetch failed for {ak_symbol}: {e}")

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from AKShare (async wrapper)."""

        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        records = []
        for row in raw_records:
            record = OHLCBase(
                symbol=symbol,
                data_source="akshare",
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                backward_factor=row["backward_factor"],
                data={"amount": row["amount"], "source": "akshare"},
            )
            records.append(record)

        return records


FetcherRegistry.register(AKShareFetcher())
