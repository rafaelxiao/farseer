import json
from datetime import datetime

from sqlalchemy import select
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

    async def create_ohlc(self, data: OHLCBase) -> OHLC:
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
