"""
API endpoints for triggering data fetch jobs.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db
from farseer.scheduler.fetch_jobs import fetch_batch, load_progress

router = APIRouter()


@router.post("/start")
async def start_fetch(
    background_tasks: BackgroundTasks,
    source: str = Query(default="baostock", description="Data source: baostock, yfinance"),
    symbols: str | None = Query(default=None, description="Comma-separated symbols (empty for all A-shares)"),
    timeframe: str = Query(default="1d", description="Timeframe: 1d, 1w, 1M"),
):
    """
    Start a batch fetch job (runs in background).

    - **source**: Data source to use
    - **symbols**: Specific symbols to fetch (comma-separated). Empty for all A-shares.
    - **timeframe**: Data timeframe
    """
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(",")] if symbols else None

    # Run in background
    background_tasks.add_task(
        fetch_batch,
        source=source,
        symbols=symbol_list,
        timeframe=timeframe,
    )

    return {
        "status": "started",
        "source": source,
        "symbols": symbol_list or "all A-shares",
        "timeframe": timeframe,
    }


@router.get("/progress")
async def get_progress():
    """Get fetch job progress."""
    progress = load_progress()
    return {
        "completed": len(progress.get("completed", [])),
        "failed": len(progress.get("failed", [])),
        "failed_symbols": progress.get("failed", []),
        "last_update": progress.get("last_update"),
    }
