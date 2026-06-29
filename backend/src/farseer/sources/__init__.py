# Import sources to register them
from farseer.sources.tushare_fetcher import TushareFetcher
from farseer.sources.akshare_fetcher import AKShareFetcher
from farseer.sources.baostock_fetcher import BaostockFetcher
from farseer.sources.yfinance_fetcher import YFinanceFetcher
from farseer.sources.binance_fetcher import BinanceFetcher

__all__ = [
    "TushareFetcher",
    "AKShareFetcher", 
    "BaostockFetcher",
    "YFinanceFetcher",
    "BinanceFetcher",
]
