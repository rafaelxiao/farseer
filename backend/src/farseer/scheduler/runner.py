import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from farseer.database import async_session_factory
from farseer.models.task import TaskRun

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


async def run_fetcher_job(job_id: str, fetcher):
    """Wrapper to run a fetcher and log the result."""
    from datetime import timezone
    run = TaskRun(job_id=job_id, status="running", started_at=datetime.now(timezone.utc))

    async with async_session_factory() as db:
        db.add(run)
        await db.commit()
        await db.refresh(run)

        try:
            result = await fetcher.run()
            run.status = result.get("status", "unknown")
            run.result = str(result)
        except Exception as e:
            run.status = "failed"
            run.result = str(e)
            logger.exception(f"Job {job_id} failed")
        finally:
            run.finished_at = datetime.now(timezone.utc)
            await db.commit()


def start_scheduler():
    """Start the scheduler and register jobs (only in prod)."""
    from farseer.config import settings
    from farseer.scheduler.jobs import register_jobs

    if not settings.enable_scheduler:
        logger.info("Scheduler disabled in dev mode")
        return

    register_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
