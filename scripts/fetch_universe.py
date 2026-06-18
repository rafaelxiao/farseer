#!/usr/bin/env python3
"""
Fetch all symbols from universe using tushare.
Skips symbols that already have data.
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from sqlalchemy import text
from farseer.database import async_session_factory
from farseer.fetchers.registry import FetcherRegistry
import farseer.fetchers.sources


DATA_DIR = Path(__file__).parent.parent / "backend" / "data"


def load_universe() -> list[str]:
    """Load CSI 300 + CSI 500 + ETF symbols (deduplicated)."""
    symbols = set()
    
    for f in ["csi300.json", "csi500.json", "etf_top100.json"]:
        path = DATA_DIR / f
        if path.exists():
            with open(path) as fh:
                symbols.update(json.load(fh))
    
    return sorted(symbols)


async def get_existing_symbols() -> set[str]:
    """Get symbols already in database."""
    async with async_session_factory() as db:
        result = await db.execute(text("SELECT DISTINCT symbol FROM ohlc"))
        return {row[0] for row in result}


async def fetch_universe():
    all_symbols = load_universe()
    existing = await get_existing_symbols()
    
    to_fetch = [s for s in all_symbols if s not in existing]
    
    logging.info(f"Universe: {len(all_symbols)} symbols")
    logging.info(f"Already in DB: {len(existing)}")
    logging.info(f"To fetch: {len(to_fetch)}")
    
    if not to_fetch:
        logging.info("Nothing to fetch!")
        return
    
    fetcher = FetcherRegistry.get("tushare")
    start_time = datetime.now()
    success = 0
    failed = 0
    
    for i, symbol in enumerate(to_fetch):
        try:
            result = await fetcher.fetch_ohlc(symbol, "1d")
            success += 1
            
            if (i + 1) % 50 == 0:
                elapsed = (datetime.now() - start_time).total_seconds() / 60
                logging.info(f"[{i+1}/{len(to_fetch)}] {success} success, {elapsed:.1f} min")
                
        except Exception as e:
            failed += 1
            logging.error(f"[{i+1}] Failed {symbol}: {e}")
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    logging.info(f"Done! {success}/{len(to_fetch)} fetched, {failed} failed, {elapsed:.1f} min")


if __name__ == "__main__":
    asyncio.run(fetch_universe())
