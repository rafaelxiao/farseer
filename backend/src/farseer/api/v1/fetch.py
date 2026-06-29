"""
API endpoints for triggering data fetch jobs.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db

router = APIRouter()


@router.post("/start")
async def start_fetch(
    background_tasks: BackgroundTasks,
    symbols: str | None = Query(default=None, description="Comma-separated symbols (empty for all)"),
):
    """
    Start a fetch job (runs in background).

    - **symbols**: Specific symbols to fetch (comma-separated). Empty for all universe symbols.
    """
    from farseer.jobs.jobs import daily_fetch_job
    
    # Run in background
    background_tasks.add_task(daily_fetch_job)

    return {
        "status": "started",
        "symbols": symbols or "all universe symbols",
    }


@router.get("/progress")
async def get_progress():
    """Get fetch job progress."""
    # Check latest task run
    from farseer.database import async_session_factory
    from farseer.models.task import TaskRun
    from sqlalchemy import select, func
    
    async with async_session_factory() as db:
        # Get latest run
        query = select(TaskRun).where(TaskRun.job_id == "daily_fetch").order_by(TaskRun.created_at.desc()).limit(1)
        result = await db.execute(query)
        latest = result.scalar_one_or_none()
        
        # Get total runs
        count_query = select(func.count(TaskRun.id)).where(TaskRun.job_id == "daily_fetch")
        total = (await db.execute(count_query)).scalar() or 0
        
        return {
            "latest_status": latest.status if latest else None,
            "latest_started": latest.started_at.isoformat() if latest and latest.started_at else None,
            "latest_finished": latest.finished_at.isoformat() if latest and latest.finished_at else None,
            "total_runs": total,
        }
