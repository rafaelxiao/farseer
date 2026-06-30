"""Valid data source names — kept in sync with registered fetchers."""

from enum import StrEnum


class DataSource(StrEnum):
    tushare = "tushare"
    baostock = "baostock"
    akshare = "akshare"
    yfinance = "yfinance"
    binance = "binance"
    qmt = "qmt"

    @classmethod
    def values(cls) -> list[str]:
        return [m.value for m in cls]
