from datetime import datetime

from pydantic import BaseModel


class OHLCBase(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0


class OHCLOut(OHLCBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OHLCQuery(BaseModel):
    symbol: str
    timeframe: str = "1d"
    start: datetime | None = None
    end: datetime | None = None
    limit: int = 1000


class OHLCBatchCreate(BaseModel):
    items: list[OHLCBase]
