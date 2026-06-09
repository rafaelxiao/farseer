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
        adjust: str = "original",
    ) -> list[dict]:
        """
        Get OHLC data with optional price adjustment.

        Adjustment types:
        - original: Actual trading prices (no adjustment)
        - forward: Forward adjusted (前复权) - recent prices real, historical adjusted DOWN
        - backward: Backward adjusted (后复权) - historical prices real, recent adjusted UP

        backward_factor stored in DB:
        - Historical: backward_factor = 1.0 (prices stay actual)
        - Recent: backward_factor > 1.0 (prices adjusted UP)
        """
        query = (
            select(OHLC)
            .where(OHLC.symbol == symbol, OHLC.timeframe == timeframe)
            .order_by(OHLC.timestamp.asc())
            .limit(limit)
        )

        if start:
            query = query.where(OHLC.timestamp >= datetime.fromisoformat(start))
        if end:
            query = query.where(OHLC.timestamp <= datetime.fromisoformat(end))

        result = await self.db.execute(query)
        rows = list(result.scalars().all())

        if not rows:
            return []

        # For forward adjustment, we need the latest backward_factor
        latest_backward_factor = float(rows[-1].backward_factor)

        records = []
        for row in rows:
            record = {
                "id": row.id,
                "symbol": row.symbol,
                "timeframe": row.timeframe,
                "timestamp": row.timestamp,
                "volume": row.volume,
                "backward_factor": float(row.backward_factor),
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

            bf = float(row.backward_factor)

            if adjust == "original":
                # Actual trading prices (no adjustment)
                record.update({
                    "open": float(row.open),
                    "high": float(row.high),
                    "low": float(row.low),
                    "close": float(row.close),
                })

            elif adjust == "backward":
                # 后复权: price * backward_factor
                # Historical prices stay actual, recent adjusted UP
                record.update({
                    "open": float(row.open) * bf,
                    "high": float(row.high) * bf,
                    "low": float(row.low) * bf,
                    "close": float(row.close) * bf,
                })

            elif adjust == "forward":
                # 前复权: price * (backward_factor / latest_backward_factor)
                # Recent prices stay actual, historical adjusted DOWN
                forward_factor = bf / latest_backward_factor if latest_backward_factor else 1.0
                record.update({
                    "open": float(row.open) * forward_factor,
                    "high": float(row.high) * forward_factor,
                    "low": float(row.low) * forward_factor,
                    "close": float(row.close) * forward_factor,
                })

            else:
                raise ValueError(f"Unknown adjust: {adjust}. Use 'original', 'forward', or 'backward'")

            records.append(record)

        return records

    async def upsert_ohlc(self, data: OHLCBase) -> OHLC:
        """Insert or update OHLC record."""
        stmt = pg_insert(OHLC).values(
            symbol=data.symbol,
            timeframe=data.timeframe,
            timestamp=data.timestamp,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            backward_factor=data.backward_factor,
            data=json.dumps(data.data) if data.data else "{}",
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": data.open,
                "high": data.high,
                "low": data.low,
                "close": data.close,
                "volume": data.volume,
                "backward_factor": data.backward_factor,
                "data": json.dumps(data.data) if data.data else "{}",
            },
        ).returning(OHLC)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def upsert_ohlc_batch(self, items: list[OHLCBase]) -> list[OHLC]:
        """Batch upsert OHLC records."""
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
                "backward_factor": item.backward_factor,
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
                "backward_factor": stmt.excluded.backward_factor,
                "data": stmt.excluded.data,
            },
        ).returning(OHLC)

        result = await self.db.execute(stmt)
        await self.db.commit()
        return list(result.scalars().all())

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
            backward_factor=data.backward_factor,
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
                backward_factor=item.backward_factor,
                data=json.dumps(item.data) if item.data else "{}",
            )
            for item in items
        ]
        self.db.add_all(ohlc_list)
        await self.db.commit()
        for ohlc in ohlc_list:
            await self.db.refresh(ohlc)
        return ohlc_list
