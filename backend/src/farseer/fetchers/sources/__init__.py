# Import sources to register them
from farseer.fetchers.sources.tushare_fetcher import TushareFetcher
from farseer.fetchers.sources.akshare_fetcher import AKShareFetcher
from farseer.fetchers.sources.baostock_fetcher import BaostockFetcher
from farseer.fetchers.sources.yfinance_fetcher import YFinanceFetcher
from farseer.fetchers.sources.binance_fetcher import BinanceFetcher

__all__ = [
    "TushareFetcher",
    "AKShareFetcher", 
    "BaostockFetcher",
    "YFinanceFetcher",
    "BinanceFetcher",
]
