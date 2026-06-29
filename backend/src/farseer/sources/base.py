"""
Base fetcher interface.

All data source fetchers inherit from this class and implement the abstract methods.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from farseer.database import async_session_factory
from farseer.schemas.ohlc import OHLCBase


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    source: str
    symbol: str
    records_added: int
    records_skipped: int
    errors: list[str]
    elapsed_seconds: float


class BaseFetcher(ABC):
    """Base class for all data source fetchers."""

    # Subclasses must set these
    name: str = "base"
    supported_exchanges: list[str] = []

    async def fetch_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
    ) -> FetchResult:
        """
        Fetch OHLC data and save to database.
        Returns FetchResult with stats.
        """
        start_time = datetime.now()
        errors = []
        added = 0
        skipped = 0

        async with async_session_factory() as db:
            try:
                # Fetch from source (subclass implements this)
                records = await self._fetch_ohlc(symbol, timeframe, start, end)

                # Save to database
                for record in records:
                    try:
                        await self._save_ohlc(db, record)
                        added += 1
                    except Exception as e:
                        errors.append(f"Save error: {e}")
                        skipped += 1

                await db.commit()

            except Exception as e:
                await db.rollback()
                errors.append(f"Fetch error: {e}")

        elapsed = (datetime.now() - start_time).total_seconds()

        return FetchResult(
            source=self.name,
            symbol=symbol,
            records_added=added,
            records_skipped=skipped,
            errors=errors,
            elapsed_seconds=elapsed,
        )

    @abstractmethod
    async def _fetch_ohlc(
        self,
        symbol: str,
        timeframe: str,
        start: str | None,
        end: str | None,
    ) -> list[OHLCBase]:
        """
        Fetch OHLC data from source.
        Must return list of OHLCBase with Farseer canonical symbols.
        """
        ...

    async def _save_ohlc(self, db: AsyncSession, record: OHLCBase) -> None:
        """Save a single OHLC record. Override for custom logic."""
        from farseer.data.ohlc import OHLCService
        service = OHLCService(db)
        await service.upsert_ohlc(record)

    def validate_symbol(self, symbol: str) -> bool:
        """Check if symbol is supported by this source."""
        from farseer.universe import SymbolFormat
        code, exchange = SymbolFormat.parse(symbol)
        return exchange.value in self.supported_exchanges
