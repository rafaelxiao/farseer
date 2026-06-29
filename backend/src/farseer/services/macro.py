"""Macro-economic data service layer."""

import json
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.macro import Macro
from farseer.schemas.macro import MacroBase

logger = logging.getLogger(__name__)


class MacroService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def query(
        self,
        symbol: Optional[str] = None,
        data_source: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 200,
    ) -> list[Macro]:
        q = select(Macro).order_by(Macro.date.desc()).limit(limit)

        if symbol:
            q = q.where(Macro.symbol == symbol)
        if data_source:
            q = q.where(Macro.data_source == data_source)
        if start_date:
            q = q.where(Macro.date >= start_date)
        if end_date:
            q = q.where(Macro.date <= end_date)

        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def list_symbols(self) -> list[dict]:
        """List available macro symbols with latest observation."""
        q = select(Macro.symbol, Macro.data_source).distinct().order_by(Macro.symbol)
        result = await self.db.execute(q)
        return [{"symbol": r[0], "data_source": r[1]} for r in result.fetchall()]

    async def upsert_batch(self, items: list[MacroBase]) -> int:
        """Batch upsert macro records. Returns count inserted."""
        if not items:
            return 0

        values = [
            {
                "symbol": item.symbol,
                "data_source": item.data_source.value if hasattr(item.data_source, "value") else item.data_source,
                "date": item.date,
                "value": item.value,
                "data": json.dumps(item.data or {}),
            }
            for item in items
        ]

        # Chunk to avoid PostgreSQL parameter limit
        total = 0
        chunk_size = 1000
        for i in range(0, len(values), chunk_size):
            chunk = values[i : i + chunk_size]
            stmt = pg_insert(Macro).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol", "data_source", "date"],
                set_={
                    "value": stmt.excluded.value,
                    "data": stmt.excluded.data,
                },
            )
            await self.db.execute(stmt)
            total += len(chunk)

        await self.db.commit()
        return total
