#!/usr/bin/env python3
"""Retry failed fundamental fetches."""
import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
from farseer.fetchers.sources.akshare_fundamentals import fetch_fundamentals

DATA_DIR = Path(__file__).parent.parent / "backend" / "data"

def get_missing_symbols() -> list[str]:
    """Find symbols in universe but not in fundamentals."""
    symbols = set()
    for f in ["csi300.json", "csi500.json", "etf_top100.json"]:
        path = DATA_DIR / f
        if path.exists():
            with open(path) as fh:
                symbols.update(json.load(fh))
    
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM fundamentals")
    fund_symbols = {row[0] for row in cur.fetchall()}
    cur.close()
    conn.close()
    
    return sorted(symbols - fund_symbols)

async def main():
    missing = get_missing_symbols()
    logging.info(f"Missing fundamentals: {len(missing)} symbols")
    
    success = 0
    failed = 0
    
    for symbol in missing:
        try:
            count = await fetch_fundamentals(symbol)
            if count > 0:
                success += 1
                logging.info(f"✓ {symbol}: {count} records")
            else:
                failed += 1
                logging.warning(f"✗ {symbol}: no data")
        except Exception as e:
            failed += 1
            logging.error(f"✗ {symbol}: {e}")
    
    logging.info(f"Done! {success} success, {failed} failed")

if __name__ == "__main__":
    asyncio.run(main())
