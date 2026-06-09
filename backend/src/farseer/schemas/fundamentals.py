from datetime import date, datetime

from pydantic import BaseModel


class FundamentalsBase(BaseModel):
    symbol: str
    date: date
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    market_cap: float | None = None
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    dividend_yield: float | None = None
    sector: str | None = None
    industry: str | None = None
    extra: str | None = None


class FundamentalsOut(FundamentalsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FundamentalsQuery(BaseModel):
    symbol: str | None = None
    sector: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: int = 100
