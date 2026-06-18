"""
OHLC service for database operations.
"""

import json
import math
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.models.ohlc import OHLC
from farseer.schemas.ohlc import OHLCBase


from zoneinfo import ZoneInfo


def _market_tz(symbol: str) -> ZoneInfo:
    """Return the market timezone for a symbol."""
    if ".SH" in symbol or ".SZ" in symbol:
        return ZoneInfo("Asia/Shanghai")
    # Future: ".US" -> America/New_York, else UTC
    return ZoneInfo("UTC")


def _format_date(ts, symbol: str) -> str:
    """Format timestamp as date string in market's local timezone."""
    return ts.astimezone(_market_tz(symbol)).strftime("%Y-%m-%d")


def safe_float(val, default=0.0):
    """Convert to float, replacing NaN/Inf with default."""
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


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
        data_source: str = "tushare",
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
            .where(OHLC.symbol == symbol, OHLC.data_source == data_source, OHLC.timeframe == timeframe)
            .order_by(OHLC.timestamp.desc())
            .limit(1)
        )
        latest_result = await self.db.execute(latest_query)
        latest_backward_factor = float(latest_result.scalar() or 1.0)

        # Get requested data
        # Default: latest N bars
        if end and not start:
            # Get last N bars before end date
            query = (
                select(OHLC)
                .where(OHLC.symbol == symbol, OHLC.data_source == data_source, OHLC.timeframe == timeframe)
                .where(OHLC.timestamp <= datetime.fromisoformat(end))
                .order_by(OHLC.timestamp.desc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            rows = list(reversed(list(result.scalars().all())))
        elif start or end:
            # Date range specified: fetch ASC
            query = (
                select(OHLC)
                .where(OHLC.symbol == symbol, OHLC.data_source == data_source, OHLC.timeframe == timeframe)
                .order_by(OHLC.timestamp.asc())
                .limit(limit)
            )
            if start:
                query = query.where(OHLC.timestamp >= datetime.fromisoformat(start))
            if end:
                query = query.where(OHLC.timestamp <= datetime.fromisoformat(end))
            result = await self.db.execute(query)
            rows = list(result.scalars().all())
        else:
            # No date range: get latest N bars
            query = (
                select(OHLC)
                .where(OHLC.symbol == symbol, OHLC.data_source == data_source, OHLC.timeframe == timeframe)
                .order_by(OHLC.timestamp.desc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            rows = list(reversed(list(result.scalars().all())))

        if not rows:
            return []

        records = []
        for row in rows:
            # For daily data, use date-only string in market's local timezone
            ts_val = row.timestamp
            if row.timeframe == "1d":
                ts_val = _format_date(row.timestamp, row.symbol)

            record = {
                "id": row.id,
                "symbol": row.symbol,
                "data_source": row.data_source,
                "timeframe": row.timeframe,
                "timestamp": ts_val,
                "volume": row.volume,
                "backward_factor": float(row.backward_factor),
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }

            bf = safe_float(row.backward_factor, 1.0)
            o = safe_float(row.open)
            h = safe_float(row.high)
            l = safe_float(row.low)
            c = safe_float(row.close)

            if adjust in ("backward", "original"):
                record.update({"open": o, "high": h, "low": l, "close": c})

            elif adjust == "forward":
                factor = latest_backward_factor / bf if bf else 1.0
                record.update({
                    "open": o * factor,
                    "high": h * factor,
                    "low": l * factor,
                    "close": c * factor,
                })

            elif adjust == "actual":
                record.update({
                    "open": o / bf if bf else o,
                    "high": h / bf if bf else h,
                    "low": l / bf if bf else l,
                    "close": c / bf if bf else c,
                })

            else:
                raise ValueError(f"Unknown adjust: {adjust}. Use 'backward', 'forward', or 'actual'")

            records.append(record)

        return records

    async def upsert_ohlc(self, data: OHLCBase) -> OHLC:
        """Insert or update OHLC record."""
        stmt = pg_insert(OHLC).values(
            symbol=data.symbol,
            data_source=data.data_source,
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
            index_elements=["symbol", "data_source", "timeframe", "timestamp"],
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
                "data_source": item.data_source,
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
            index_elements=["symbol", "data_source", "timeframe", "timestamp"],
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
