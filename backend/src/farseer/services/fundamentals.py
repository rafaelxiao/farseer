from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.fundamentals import Fundamentals
from farseer.schemas.fundamentals import FundamentalsBase


class FundamentalsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_fundamentals(
        self,
        symbol: str | None = None,
        sector: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> list[Fundamentals]:
        query = select(Fundamentals).order_by(Fundamentals.date.desc()).limit(limit)

        if symbol:
            query = query.where(Fundamentals.symbol == symbol)
        if sector:
            query = query.where(Fundamentals.sector == sector)
        if start_date:
            query = query.where(Fundamentals.date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(Fundamentals.date <= date.fromisoformat(end_date))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_fundamentals(self, data: FundamentalsBase) -> Fundamentals:
        fund = Fundamentals(**data.model_dump())
        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)
        return fund
