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
        adjust: str = "backward",
    ) -> list[dict]:
        """
        Get OHLC data with optional price adjustment.

        Stored data: 后复权 (backward-adjusted) prices with backward_factor.

        Adjustment types:
        - backward: 后复权 (stored prices, immutable)
        - forward: 前复权 (for backtesting, recent prices actual)
        - actual: Actual price at that time
        """
        # Get latest backward_factor FIRST (for forward conversion)
        latest_query = (
            select(OHLC.backward_factor)
            .where(OHLC.symbol == symbol, OHLC.timeframe == timeframe)
            .order_by(OHLC.timestamp.desc())
            .limit(1)
        )
        latest_result = await self.db.execute(latest_query)
        latest_backward_factor = float(latest_result.scalar() or 1.0)

        # Get requested data
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

            if adjust == "backward":
                # 后复权: stored prices (immutable)
                record.update({
                    "open": float(row.open),
                    "high": float(row.high),
                    "low": float(row.low),
                    "close": float(row.close),
                })

            elif adjust == "forward":
                # 前复权: for backtesting
                # forward = backward / backward_factor * latest_backward_factor
                factor = latest_backward_factor / bf if bf else 1.0
                record.update({
                    "open": float(row.open) * factor,
                    "high": float(row.high) * factor,
                    "low": float(row.low) * factor,
                    "close": float(row.close) * factor,
                })

            elif adjust == "actual":
                # Actual price at that time
                # actual = backward / backward_factor
                record.update({
                    "open": float(row.open) / bf if bf else float(row.open),
                    "high": float(row.high) / bf if bf else float(row.high),
                    "low": float(row.low) / bf if bf else float(row.low),
                    "close": float(row.close) / bf if bf else float(row.close),
                })

            else:
                raise ValueError(f"Unknown adjust: {adjust}. Use 'backward', 'forward', or 'actual'")

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
