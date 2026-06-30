"""Macro-economic data schemas for API serialization."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, field_validator

from farseer.sources.datasource import DataSource


class MacroBase(BaseModel):
    symbol: str
    data_source: DataSource = DataSource.akshare
    date: date
    value: float
    data: dict[str, Any] | None = None

    @field_validator("data", mode="before")
    @classmethod
    def coerce_data(cls, v: Any) -> Any:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


class MacroOut(MacroBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MacroQuery(BaseModel):
    symbol: str | None = None
    data_source: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    limit: int = 200
