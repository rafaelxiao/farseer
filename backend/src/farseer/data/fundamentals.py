import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.fundamentals import Fundamentals
from farseer.schemas.fundamentals import FundamentalsBase


class FundamentalsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fundamentals(
        self,
        symbol: str | None = None,
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> list[Fundamentals]:
        query = select(Fundamentals).order_by(Fundamentals.date.desc()).limit(limit)

        if symbol:
            query = query.where(Fundamentals.symbol == symbol)
        if category:
            query = query.where(Fundamentals.category == category)
        if start_date:
            query = query.where(Fundamentals.date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(Fundamentals.date <= date.fromisoformat(end_date))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def upsert_fundamentals(self, data: FundamentalsBase) -> Fundamentals:
        """
        Insert or update fundamentals record.
        If (symbol, date, category) exists, update it.
        """
        stmt = pg_insert(Fundamentals).values(
            symbol=data.symbol,
            data_source=data.data_source,
            date=data.date,
            category=data.category,
            data=json.dumps(data.data),
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "data_source", "date", "category"],
            set_={
                "data": json.dumps(data.data),
            },
        ).returning(Fundamentals)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def upsert_fundamentals_batch(self, items: list[FundamentalsBase]) -> list[Fundamentals]:
        """Batch upsert fundamentals records."""
        if not items:
            return []

        values = [
            {
                "symbol": item.symbol,
                "data_source": item.data_source,
                "date": item.date,
                "category": item.category,
                "data": json.dumps(item.data),
            }
            for item in items
        ]

        stmt = pg_insert(Fundamentals).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "data_source", "date", "category"],
            set_={
                "data": stmt.excluded.data,
            },
        ).returning(Fundamentals)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return list(result.scalars().all())

    # Keep old method for backwards compatibility
    async def create_fundamentals(self, data: FundamentalsBase) -> Fundamentals:
        """Insert only (will raise on duplicate)."""
        fund = Fundamentals(
            symbol=data.symbol,
            data_source=data.data_source,
            date=data.date,
            category=data.category,
            data=json.dumps(data.data),
        )
        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)
        return fund
