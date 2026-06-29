"""Macro-economic data API endpoints."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db
from farseer.schemas.macro import MacroBase, MacroOut
from farseer.services.macro import MacroService

router = APIRouter()


@router.get("/", response_model=list[MacroOut])
async def get_macro(
    symbol: Optional[str] = Query(None, description="Macro symbol, e.g. CPI.CN, PMI.CN"),
    data_source: Optional[str] = Query(None, description="Data source, e.g. akshare"),
    start_date: Optional[date] = Query(None, description="Start date (inclusive)"),
    end_date: Optional[date] = Query(None, description="End date (inclusive)"),
    limit: int = Query(200, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    """Query macro-economic data."""
    service = MacroService(db)
    return await service.query(
        symbol=symbol, data_source=data_source,
        start_date=start_date, end_date=end_date, limit=limit,
    )


@router.get("/symbols")
async def list_macro_symbols(db: AsyncSession = Depends(get_db)):
    """List all available macro indicators."""
    service = MacroService(db)
    return await service.list_symbols()


@router.post("/batch", response_model=dict)
async def upsert_macro_batch(
    items: list[MacroBase],
    db: AsyncSession = Depends(get_db),
):
    """Batch insert/update macro records."""
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")
    service = MacroService(db)
    count = await service.upsert_batch(items)
    return {"count": count}
