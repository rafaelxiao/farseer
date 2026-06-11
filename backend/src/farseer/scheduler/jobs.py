import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from farseer.fetchers.registry import FetcherRegistry
from farseer.universe.registry import UniverseRegistry

logger = logging.getLogger(__name__)


async def daily_fetch_job():
    """Daily fetch: update all universe symbols with latest data."""
    symbols = UniverseRegistry.get_fetch_universe()
    
    if not symbols:
        logger.warning("No symbols in universe, skipping daily fetch")
        return
    
    logger.info(f"Daily fetch: updating {len(symbols)} symbols")
    fetcher = FetcherRegistry.get("baostock")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            result = await fetcher.fetch_ohlc(symbol, "1d")
            if result.records_added > 0:
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            failed += 1
    
    logger.info(f"Daily fetch complete: {success} success, {failed} failed")


def register_jobs(scheduler: AsyncIOScheduler):
    """Register scheduled jobs."""
    
    # Daily fetch: run at 18:00 (after China market close at 15:00)
    scheduler.add_job(
        daily_fetch_job,
        trigger=CronTrigger(hour=18, minute=0),
        id="daily_fetch",
        name="Daily Universe Fetch",
        replace_existing=True,
    )
    
    logger.info("Registered jobs: daily_fetch (18:00)")
