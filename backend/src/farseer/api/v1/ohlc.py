from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from farseer.api.deps import get_db
from farseer.schemas.ohlc import OHLCBase, OHCLOut, OHLCQuery, OHLCBatchCreate
from farseer.data.ohlc import OHLCService

router = APIRouter()


@router.get("/symbols")
async def list_symbols(
    data_source: str = "tushare",
    db: AsyncSession = Depends(get_db),
):
    """List all symbols with record counts."""
    result = await db.execute(text("""
        SELECT symbol, COUNT(*) as records, MAX(timestamp) as latest
        FROM ohlc
        WHERE data_source = :src
        GROUP BY symbol
        ORDER BY symbol
    """), {"src": data_source})
    return [
        {"symbol": row[0], "records": row[1], "latest": row[2]}
        for row in result
    ]


@router.get("/")
async def get_ohlc(
    symbol: str | None = None,
    symbols: str | None = None,
    timeframe: str = "1d",
    start: str | None = None,
    end: str | None = None,
    limit: int = 1000,
    adjust: str = Query(
        default="original",
        description="Adjustment type: 'original' (actual prices), 'forward' (前复权), 'backward' (后复权)"
    ),
    data_source: str = Query(
        default="tushare",
        description="Data source: tushare (1d), qmt (1m/5m), baostock, akshare, yfinance, binance"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get OHLC data with optional price adjustment.

    - **symbol**: Single symbol (e.g. 600519.SH)
    - **symbols**: Comma-separated symbols (e.g. 600519.SH,000001.SZ)
    - **start/end**: ISO date (2026-01-01) or YYYYMMDD (20260101)
    - **original**: Actual trading prices (no adjustment)
    - **forward**: Forward adjusted (前复权) - recent prices real, historical adjusted down
    - **backward**: Backward adjusted (后复权) - historical prices real, recent adjusted up
    """
    service = OHLCService(db)
    return await service.get_ohlc(symbol, symbols, timeframe, start, end, limit, adjust, data_source=data_source)


@router.post("/", response_model=OHCLOut)
async def upsert_ohlc(
    data: OHLCBase,
    db: AsyncSession = Depends(get_db),
):
    """Insert or update OHLC record (upsert)."""
    service = OHLCService(db)
    return await service.upsert_ohlc(data)


@router.post("/batch", response_model=list[OHCLOut])
async def upsert_ohlc_batch(
    data: OHLCBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """Batch upsert OHLC records."""
    service = OHLCService(db)
    return await service.upsert_ohlc_batch(data.items)
