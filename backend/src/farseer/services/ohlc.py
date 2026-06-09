import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.ohlc import OHLC
from farseer.schemas.ohlc import OHLCBase


class OHLCService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ohlc(
        self,
        symbol: str,
        timeframe: str = "1d",
        start: str | None = None,
        end: str | None = None,
        limit: int = 1000,
    ) -> list[OHLC]:
        query = (
            select(OHLC)
            .where(OHLC.symbol == symbol, OHLC.timeframe == timeframe)
            .order_by(OHLC.timestamp.desc())
            .limit(limit)
        )

        if start:
            query = query.where(OHLC.timestamp >= datetime.fromisoformat(start))
        if end:
            query = query.where(OHLC.timestamp <= datetime.fromisoformat(end))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def upsert_ohlc(self, data: OHLCBase) -> OHLC:
        """
        Insert or update OHLC record.
        If (symbol, timeframe, timestamp) exists, update it.
        """
        stmt = pg_insert(OHLC).values(
            symbol=data.symbol,
            timeframe=data.timeframe,
            timestamp=data.timestamp,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            adjustor_factor=data.adjustor_factor,
            data=json.dumps(data.data) if data.data else "{}",
        )

        # On conflict, update all fields except the unique key
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": data.open,
                "high": data.high,
                "low": data.low,
                "close": data.close,
                "volume": data.volume,
                "adjustor_factor": data.adjustor_factor,
                "data": json.dumps(data.data) if data.data else "{}",
            },
        ).returning(OHLC)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def upsert_ohlc_batch(self, items: list[OHLCBase]) -> list[OHLC]:
        """
        Batch upsert OHLC records.
        Uses single INSERT ... ON CONFLICT for efficiency.
        """
        if not items:
            return []

        values = [
            {
                "symbol": item.symbol,
                "timeframe": item.timeframe,
                "timestamp": item.timestamp,
                "open": item.open,
                "high": item.high,
                "low": item.low,
                "close": item.close,
                "volume": item.volume,
                "adjustor_factor": item.adjustor_factor,
                "data": json.dumps(item.data) if item.data else "{}",
            }
            for item in items
        ]

        stmt = pg_insert(OHLC).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "adjustor_factor": stmt.excluded.adjustor_factor,
                "data": stmt.excluded.data,
            },
        ).returning(OHLC)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return list(result.scalars().all())

    # Keep old methods for backwards compatibility
    async def create_ohlc(self, data: OHLCBase) -> OHLC:
        """Insert only (will raise on duplicate)."""
        ohlc = OHLC(
            symbol=data.symbol,
            timeframe=data.timeframe,
            timestamp=data.timestamp,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            adjustor_factor=data.adjustor_factor,
            data=json.dumps(data.data) if data.data else "{}",
        )
        self.db.add(ohlc)
        await self.db.commit()
        await self.db.refresh(ohlc)
        return ohlc

    async def create_ohlc_batch(self, items: list[OHLCBase]) -> list[OHLC]:
        """Insert only (will raise on duplicate)."""
        ohlc_list = [
            OHLC(
                symbol=item.symbol,
                timeframe=item.timeframe,
                timestamp=item.timestamp,
                open=item.open,
                high=item.high,
                low=item.low,
                close=item.close,
                volume=item.volume,
                adjustor_factor=item.adjustor_factor,
                data=json.dumps(item.data) if item.data else "{}",
            )
            for item in items
        ]
        self.db.add_all(ohlc_list)
        await self.db.commit()
        for ohlc in ohlc_list:
            await self.db.refresh(ohlc)
        return ohlc_list
