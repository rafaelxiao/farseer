from sqlalchemy.ext.asyncio import AsyncSession

from farseer.fetchers.base import BaseFetcher


class ExampleFetcher(BaseFetcher):
    """Example fetcher - replace with real data source."""

    name = "example"

    async def fetch(self, db: AsyncSession) -> dict:
        # TODO: Implement actual data fetching logic
        # Example: fetch from Yahoo Finance, Alpha Vantage, etc.
        #
        # from farseer.models.ohlc import OHLC
        # ohlc = OHLC(symbol="AAPL", timeframe="1d", ...)
        # db.add(ohlc)
        #
        return {"records_added": 0, "message": "Example fetcher - not implemented"}
