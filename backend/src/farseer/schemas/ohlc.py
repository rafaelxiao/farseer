from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator

from farseer.sources.datasource import DataSource


class OHLCBase(BaseModel):
    symbol: str
    data_source: DataSource = DataSource.tushare
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    backward_factor: float = 1.0  # Backward adjustment (后复权): price * factor
    data: Any = {}  # Flexible extra data (JSONB in DB, may come as string from ORM)

    @field_validator("data", mode="before")
    @classmethod
    def coerce_data(cls, v: Any) -> Any:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


class OHCLOut(OHLCBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OHLCQuery(BaseModel):
    symbol: str
    data_source: DataSource = DataSource.tushare
    timeframe: str = "1d"
    start: datetime | None = None
    end: datetime | None = None
    limit: int = 1000
    adjust: str = "original"  # "original", "forward", "backward"


class OHLCBatchCreate(BaseModel):
    items: list[OHLCBase]
