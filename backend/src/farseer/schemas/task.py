from datetime import datetime

from pydantic import BaseModel


class TaskRunOut(BaseModel):
    id: int
    job_id: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskRunSummary(BaseModel):
    job_id: str
    last_run: datetime | None = None
    last_status: str | None = None
    next_run: datetime | None = None
    total_runs: int = 0
