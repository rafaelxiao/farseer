#!/usr/bin/env python3
"""
Fetch fundamental data for all symbols in universe.
ETFs get ETF-specific data (IOPV, discount rate, etc.)
Stocks get financial data (EPS, ROE, dividends, etc.)
"""
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

from farseer.fetchers.sources.akshare_fundamentals import fetch_all_fundamentals, _is_etf


DATA_DIR = Path(__file__).parent.parent / "backend" / "data"


def load_universe() -> list[str]:
    """Load all symbols from universe."""
    symbols = set()
    for f in ["csi300.json", "csi500.json", "etf_top100.json"]:
        path = DATA_DIR / f
        if path.exists():
            with open(path) as fh:
                symbols.update(json.load(fh))
    return sorted(symbols)


async def main():
    symbols = load_universe()

    stocks = [s for s in symbols if not _is_etf(s)]
    etfs = [s for s in symbols if _is_etf(s)]

    logging.info(f"Universe: {len(symbols)} total ({len(stocks)} stocks, {len(etfs)} ETFs)")
    logging.info(f"Starting fundamentals fetch...")

    start_time = datetime.now()

    result = await fetch_all_fundamentals(symbols)

    elapsed = (datetime.now() - start_time).total_seconds() / 60
    logging.info(f"Done! {result['success']} success, {result['failed']} failed, {elapsed:.1f} min")


if __name__ == "__main__":
    asyncio.run(main())
