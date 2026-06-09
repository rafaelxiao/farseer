from abc import ABC, abstractmethod
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from farseer.database import async_session_factory


class BaseFetcher(ABC):
    """Base class for data fetchers."""

    name: str = "base"

    async def run(self) -> dict:
        """Execute the fetcher. Returns result summary."""
        async with async_session_factory() as db:
            try:
                result = await self.fetch(db)
                await db.commit()
                return {"status": "success", "fetcher": self.name, "result": result}
            except Exception as e:
                await db.rollback()
                return {"status": "error", "fetcher": self.name, "error": str(e)}

    @abstractmethod
    async def fetch(self, db: AsyncSession) -> dict:
        """Implement the actual fetch logic."""
        ...
