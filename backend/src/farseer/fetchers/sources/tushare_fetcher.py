"""
Tushare data source fetcher.

Stores 后复权 (backward-adjusted) prices with backward_factor.

For stocks: Uses pro_bar(adj='hfq') and adj_factor()
For ETFs: Uses fund_daily() and fund_adj()

ETF codes: SH 51xxxx/58xxxx, SZ 15xxxx
Stock codes: everything else

Tushare symbol format: {CODE}.{EXCHANGE} (e.g., 600519.SH, 159915.SZ)
Same as Farseer internal format.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from farseer.fetchers.base import BaseFetcher
from farseer.fetchers.registry import FetcherRegistry
from farseer.schemas.ohlc import OHLCBase
from farseer.config import settings
from farseer.symbols.utils import is_etf
from farseer.universe.sets import INDICES


_executor = ThreadPoolExecutor(max_workers=2)


class TushareFetcher(BaseFetcher):
    """Fetch data from tushare (Chinese A-share + ETF data)."""

    name = "tushare"
    supported_exchanges = ["SH", "SZ"]

    def _fetch_stock(self, ts_code: str, start_date: str, end_date: str) -> list[dict]:
        """Fetch stock data: 后复权 = daily_price × adj_factor (normalized)."""
        from farseer.utils.tushare import get_tushare_pro

        pro = get_tushare_pro()

        # Fetch actual prices (not adjusted)
        df_daily = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df_daily is None or len(df_daily) == 0:
            return []

        # Fetch adjustment factors
        time.sleep(0.1)
        df_adj = pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df_adj is None or len(df_adj) == 0:
            adj_factors = {}
        else:
            adj_factors = dict(zip(df_adj["trade_date"], df_adj["adj_factor"]))

        # Normalize to first available factor in range
        df_daily = df_daily.sort_values("trade_date")
        first_adj = adj_factors.get(df_daily.iloc[0]["trade_date"], 1.0)

        records = []
        for _, row in df_daily.iterrows():
            trade_date = row["trade_date"]
            raw_adj = adj_factors.get(trade_date, first_adj)
            bf = raw_adj / first_adj if first_adj > 0 else 1.0

            records.append({
                "date": trade_date,
                "open": float(row["open"]) * bf if row["open"] else 0,
                "high": float(row["high"]) * bf if row["high"] else 0,
                "low": float(row["low"]) * bf if row["low"] else 0,
                "close": float(row["close"]) * bf if row["close"] else 0,
                "volume": int(float(row["vol"])) if row["vol"] else 0,
                "amount": float(row["amount"]) * 1000 if row["amount"] else 0,
                "backward_factor": round(bf, 10),
            })

        return records

    def _fetch_etf(self, ts_code: str, start_date: str, end_date: str) -> list[dict]:
        """Fetch ETF data using fund_daily + fund_adj.
        
        ETFs store actual prices (not 后复权). backward_factor is metadata only.
        """
        import tushare as ts
        from farseer.utils.tushare import get_tushare_pro

        pro = get_tushare_pro()

        # Fetch fund daily prices (actual, not adjusted)
        df_daily = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df_daily is None or len(df_daily) == 0:
            return []

        # Fetch fund adjustment factors
        df_adj = pro.fund_adj(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df_adj is not None and len(df_adj) > 0:
            adj_map = dict(zip(df_adj["trade_date"], df_adj["adj_factor"]))
        else:
            adj_map = {}

        df_daily = df_daily.sort_values("trade_date")

        records = []
        for _, row in df_daily.iterrows():
            trade_date = row["trade_date"]
            bf = adj_map.get(trade_date, 1.0)

            # Store actual prices (fund_daily prices, NOT multiplied by bf)
            records.append({
                "date": trade_date,
                "open": float(row["open"]) if row["open"] else 0,
                "high": float(row["high"]) if row["high"] else 0,
                "low": float(row["low"]) if row["low"] else 0,
                "close": float(row["close"]) if row["close"] else 0,
                "volume": int(float(row["vol"])) if row["vol"] else 0,
                "amount": float(row["amount"]) * 1000 if row["amount"] else 0,
                "backward_factor": round(bf, 10),
            })

        return records

    def _fetch_index(self, ts_code: str, start_date: str, end_date: str) -> list[dict]:
        """Fetch index data using index_daily. No adjustment factor."""
        from farseer.utils.tushare import get_tushare_pro

        pro = get_tushare_pro()

        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df is None or len(df) == 0:
            return []

        df = df.sort_values("trade_date")

        records = []
        for _, row in df.iterrows():
            records.append({
                "date": row["trade_date"],
                "open": float(row["open"]) if row["open"] else 0,
                "high": float(row["high"]) if row["high"] else 0,
                "low": float(row["low"]) if row["low"] else 0,
                "close": float(row["close"]) if row["close"] else 0,
                "volume": int(float(row["vol"])) if row["vol"] else 0,
                "amount": float(row["amount"]) if row["amount"] else 0,
                "backward_factor": 1.0,
            })

        return records

    def _fetch_sync(
        self,
        symbol: str,
        timeframe: str,
        start: str | None,
        end: str | None,
    ) -> list[dict]:
        """Sync fetch from tushare (runs in thread)."""
        ts_code = symbol
        start_date = start[:10].replace("-", "") if start else "19900101"
        end_date = end[:10].replace("-", "") if end else datetime.now().strftime("%Y%m%d")

        if timeframe != "1d":
            raise ValueError(f"Tushare only supports 1d timeframe, got: {timeframe}")

        try:
            time.sleep(0.1)
            
            if symbol in INDICES:
                return self._fetch_index(ts_code, start_date, end_date)
            elif is_etf(symbol):
                return self._fetch_etf(ts_code, start_date, end_date)
            else:
                return self._fetch_stock(ts_code, start_date, end_date)
        except Exception as e:
            raise Exception(f"Tushare fetch failed for {ts_code}: {e}")

    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> list[OHLCBase]:
        """Fetch OHLC from tushare (async wrapper)."""

        loop = asyncio.get_event_loop()
        raw_records = await loop.run_in_executor(
            _executor, self._fetch_sync, symbol, timeframe, start, end,
        )

        records = []
        for row in raw_records:
            record = OHLCBase(
                symbol=symbol,
                data_source="tushare",
                timeframe=timeframe,
                timestamp=datetime.strptime(row["date"], "%Y%m%d"),
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                backward_factor=row["backward_factor"],
                data={"amount": row["amount"], "source": "tushare"},
            )
            records.append(record)

        return records


FetcherRegistry.register(TushareFetcher())
