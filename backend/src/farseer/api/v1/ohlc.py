from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db
from farseer.schemas.ohlc import OHLCBase, OHCLOut, OHLCQuery, OHLCBatchCreate
from farseer.services.ohlc import OHLCService

router = APIRouter()


@router.get("/", response_model=list[OHCLOut])
async def get_ohlc(
    symbol: str,
    timeframe: str = "1d",
    start: str | None = None,
    end: str | None = None,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
):
    service = OHLCService(db)
    return await service.get_ohlc(symbol, timeframe, start, end, limit)


@router.post("/", response_model=OHCLOut)
async def create_ohlc(
    data: OHLCBase,
    db: AsyncSession = Depends(get_db),
):
    service = OHLCService(db)
    return await service.create_ohlc(data)


@router.post("/batch", response_model=list[OHCLOut])
async def create_ohlc_batch(
    data: OHLCBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    service = OHLCService(db)
    return await service.create_ohlc_batch(data.items)
