"""
Batch fetch job for downloading historical data.

Features:
- Rate limiting (respects API limits)
- Retry with exponential backoff
- Progress tracking
- Resume capability (skips already fetched symbols)
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, func

from farseer.database import async_session_factory
from farseer.fetchers.registry import FetcherRegistry
from farseer.models.ohlc import OHLC
from farseer.symbols.formats import SymbolFormat, Exchange
from farseer.symbols.converter import SymbolConverter

logger = logging.getLogger(__name__)

# Progress file location
PROGRESS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "fetch_progress.json"


def load_progress() -> dict:
    """Load fetch progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_update": None}


def save_progress(progress: dict):
    """Save fetch progress to file."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    progress["last_update"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def get_all_a_share_symbols() -> list[str]:
    """
    Get all A-share stock symbols.
    Returns list of symbols in Farseer format (e.g., "600519.SH").
    """
    import baostock as bs

    bs.login()
    try:
        # Get all stock codes
        rs = bs.query_stock_basic()
        symbols = []
        while rs.next():
            row = rs.get_row_data()
            code = row[0]  # e.g., "sh.600519"
            stock_type = row[4]  # 1=stock, 2=index, etc.

            # Only stocks (type=1)
            if stock_type == "1":
                # Convert to Farseer format
                try:
                    farseer_sym = SymbolConverter.from_baostock(code)
                    symbols.append(farseer_sym)
                except:
                    pass  # Skip invalid symbols

        return symbols
    finally:
        bs.logout()


async def fetch_single_symbol(
    source: str,
    symbol: str,
    timeframe: str = "1d",
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> dict:
    """
    Fetch a single symbol with retry logic.
    """
    fetcher = FetcherRegistry.get(source)
    if not fetcher:
        return {"symbol": symbol, "status": "error", "error": f"Unknown source: {source}"}

    for attempt in range(max_retries):
        try:
            result = await fetcher.fetch_ohlc(symbol, timeframe)
            return {
                "symbol": symbol,
                "status": "success",
                "records": result.records_added,
                "elapsed": result.elapsed_seconds,
            }
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {symbol}: {e}. Waiting {delay}s...")
                await asyncio.sleep(delay)
            else:
                return {
                    "symbol": symbol,
                    "status": "error",
                    "error": str(e),
                }


async def fetch_batch(
    source: str = "baostock",
    symbols: list[str] | None = None,
    timeframe: str = "1d",
    rate_limit_delay: float = 0.5,  # Delay between symbols
    batch_size: int = 50,  # Save progress every N symbols
):
    """
    Fetch historical data for multiple symbols.

    Features:
    - Rate limiting between requests
    - Retry with exponential backoff
    - Progress tracking (resume capability)
    - Batch progress saves
    """
    # Import sources to register fetchers
    import farseer.fetchers.sources  # noqa: F401

    # Get symbols to fetch
    if symbols is None:
        logger.info("Fetching all A-share symbols...")
        symbols = get_all_a_share_symbols()
        logger.info(f"Found {len(symbols)} symbols")

    # Load progress (for resume)
    progress = load_progress()
    completed = set(progress.get("completed", []))

    # Filter out already completed
    pending = [s for s in symbols if s not in completed]
    logger.info(f"Pending: {len(pending)} (already completed: {len(completed)})")

    # Stats
    stats = {
        "total": len(symbols),
        "completed": len(completed),
        "success": 0,
        "failed": 0,
        "records": 0,
        "start_time": datetime.now().isoformat(),
    }

    # Fetch each symbol
    for i, symbol in enumerate(pending):
        try:
            logger.info(f"[{i + 1}/{len(pending)}] Fetching {symbol}...")
            result = await fetch_single_symbol(source, symbol, timeframe)

            if result["status"] == "success":
                stats["success"] += 1
                stats["records"] += result.get("records", 0)
                completed.add(symbol)
                progress["completed"] = list(completed)
                logger.info(f"  ✓ {symbol}: {result.get('records', 0)} records in {result.get('elapsed', 0):.1f}s")
            else:
                stats["failed"] += 1
                if symbol not in progress.get("failed", []):
                    progress.setdefault("failed", []).append(symbol)
                logger.error(f"  ✗ {symbol}: {result.get('error', 'Unknown error')}")

            # Save progress periodically
            if (i + 1) % batch_size == 0:
                save_progress(progress)
                logger.info(f"Progress saved ({len(completed)}/{len(symbols)})")

            # Rate limiting
            if i < len(pending) - 1:  # Don't delay after last symbol
                await asyncio.sleep(rate_limit_delay)

        except KeyboardInterrupt:
            logger.info("Interrupted! Saving progress...")
            save_progress(progress)
            break
        except Exception as e:
            logger.error(f"Unexpected error for {symbol}: {e}")
            stats["failed"] += 1

    # Final save
    stats["end_time"] = datetime.now().isoformat()
    save_progress(progress)

    # Summary
    logger.info("=" * 60)
    logger.info(f"Fetch complete!")
    logger.info(f"  Total symbols: {stats['total']}")
    logger.info(f"  Success: {stats['success']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Total records: {stats['records']:,}")
    logger.info("=" * 60)

    return stats


# CLI entry point
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    # Parse args
    source = sys.argv[1] if len(sys.argv) > 1 else "baostock"
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1d"

    logger.info(f"Starting fetch: source={source}, timeframe={timeframe}")

    # Run
    asyncio.run(fetch_batch(source=source, timeframe=timeframe))
