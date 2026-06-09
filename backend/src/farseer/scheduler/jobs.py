from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from farseer.fetchers.example import ExampleFetcher
from farseer.scheduler.runner import run_fetcher_job


def register_jobs(scheduler: AsyncIOScheduler):
    """Register all scheduled jobs."""

    # Example: Run example fetcher every hour
    scheduler.add_job(
        run_fetcher_job,
        trigger=IntervalTrigger(hours=1),
        args=["example_fetcher", ExampleFetcher()],
        id="example_fetcher",
        name="Example Data Fetcher",
        replace_existing=True,
    )

    # Add more jobs here:
    # scheduler.add_job(
    #     run_fetcher_job,
    #     trigger=CronTrigger(hour=6, minute=0),  # Daily at 6 AM
    #     args=["daily_fundamentals", FundamentalsFetcher()],
    #     id="daily_fundamentals",
    #     name="Daily Fundamentals Update",
    #     replace_existing=True,
    # )
