from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.api.deps import get_db
from farseer.models.task import TaskRun
from farseer.schemas.task import TaskRunOut, TaskRunSummary
from farseer.jobs.runner import scheduler

router = APIRouter()


@router.get("/", response_model=list[TaskRunOut])
async def get_task_runs(
    job_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(TaskRun).order_by(TaskRun.created_at.desc()).limit(limit)
    if job_id:
        query = query.where(TaskRun.job_id == job_id)
    if status:
        query = query.where(TaskRun.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs", response_model=list[TaskRunSummary])
async def get_jobs(db: AsyncSession = Depends(get_db)):
    """List all registered jobs with summary info."""
    jobs = []
    for job in scheduler.get_jobs():
        last_run_query = (
            select(TaskRun)
            .where(TaskRun.job_id == job.id)
            .order_by(TaskRun.created_at.desc())
            .limit(1)
        )
        result = await db.execute(last_run_query)
        last_run = result.scalar_one_or_none()

        count_query = select(func.count(TaskRun.id)).where(TaskRun.job_id == job.id)
        total = (await db.execute(count_query)).scalar() or 0

        jobs.append(TaskRunSummary(
            job_id=job.id,
            last_run=last_run.created_at if last_run else None,
            last_status=last_run.status if last_run else None,
            next_run=job.next_run_time,
            total_runs=total,
        ))
    return jobs


@router.post("/trigger/{job_id}")
async def trigger_job(job_id: str, background_tasks: BackgroundTasks):
    """Manually trigger a job."""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    
    # Run the job in background
    background_tasks.add_task(job.func)
    
    return {"status": "triggered", "job_id": job_id}
