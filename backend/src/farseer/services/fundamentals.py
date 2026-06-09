import json
from datetime import date

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

    async def create_fundamentals(self, data: FundamentalsBase) -> Fundamentals:
        fund = Fundamentals(
            symbol=data.symbol,
            date=data.date,
            category=data.category,
            data=json.dumps(data.data),
        )
        self.db.add(fund)
        await self.db.commit()
        await self.db.refresh(fund)
        return fund
