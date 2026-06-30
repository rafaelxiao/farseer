from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator

from farseer.sources.datasource import DataSource


class FundamentalsBase(BaseModel):
    symbol: str
    data_source: DataSource = DataSource.tushare
    date: date
    category: str | None = None
    data: Any = {}  # Flexible JSON — stored as string in DB, parsed on read

    @field_validator("data", mode="before")
    @classmethod
    def coerce_data(cls, v: Any) -> Any:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


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
