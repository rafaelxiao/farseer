from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from farseer.fetchers.registry import FetcherRegistry
from farseer.scheduler.runner import run_fetcher_job


async def run_symbol_fetch(source: str, symbol: str, timeframe: str = "1d"):
    """Fetch a single symbol from a source."""
    fetcher = FetcherRegistry.get(source)
    if not fetcher:
        raise ValueError(f"Unknown source: {source}")
    return await fetcher.fetch_ohlc(symbol, timeframe)


def register_jobs(scheduler: AsyncIOScheduler):
    """Register scheduled jobs."""

    # Example: Fetch specific symbols daily
    # Uncomment and customize as needed:

    # scheduler.add_job(
    #     run_symbol_fetch,
    #     trigger=IntervalTrigger(hours=1),
    #     args=["yfinance", "600519.SH", "1d"],
    #     id="fetch_moutai",
    #     name="Fetch Moutai Daily",
    #     replace_existing=True,
    # )

    # scheduler.add_job(
    #     run_symbol_fetch,
    #     trigger=IntervalTrigger(hours=1),
    #     args=["yfinance", "000858.SZ", "1d"],
    #     id="fetch_wuliangye",
    #     name="Fetch Wuliangye Daily",
    #     replace_existing=True,
    # )

    pass  # Add your scheduled jobs here
