from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db
from farseer.schemas.fundamentals import FundamentalsBase, FundamentalsOut, FundamentalsQuery
from farseer.services.fundamentals import FundamentalsService

router = APIRouter()


@router.get("/", response_model=list[FundamentalsOut])
async def get_fundamentals(
    symbol: str | None = None,
    sector: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = FundamentalsService(db)
    return await service.get_fundamentals(symbol, sector, start_date, end_date, limit)


@router.post("/", response_model=FundamentalsOut)
async def create_fundamentals(
    data: FundamentalsBase,
    db: AsyncSession = Depends(get_db),
):
    service = FundamentalsService(db)
    return await service.create_fundamentals(data)
