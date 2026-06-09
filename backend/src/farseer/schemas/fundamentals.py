from datetime import date, datetime

from pydantic import BaseModel


class FundamentalsBase(BaseModel):
    symbol: str
    date: date
    category: str | None = None
    data: dict = {}  # Any fields you want: {"pe_ratio": 15.2, "revenue": 1000000, ...}


class FundamentalsOut(FundamentalsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FundamentalsQuery(BaseModel):
    symbol: str | None = None
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: int = 100
