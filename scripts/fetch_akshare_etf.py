#!/usr/bin/env python3
"""
Fetch ETF OHLC data from AKShare Sina source (fund_etf_hist_sina).

Sina is more lenient than Eastmoney — no rate limiting issues.
Symbol format: sh510050, sz159915 (Sina prefix).

Design:
  - Stores actual/hfq prices, backward_factor=1.0
  - Sina provides raw (不复权) data; Eastmoney needed for hfq/raw ratio
  - backward_factor can be updated later via SQL UPDATE (no re-fetch needed)
  - Resumes: skips dates already in DB

Usage:
  cd /home/ubuntu/projects/farseer && source backend/.venv/bin/activate
  PYTHONPATH=backend/src python3 scripts/fetch_akshare_etf.py
"""

import json
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import psycopg2
import akshare as ak

from farseer.config import settings
from farseer.data.universe import ETF_TOP100

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

DELAY = 3  # seconds — Sina tolerates this


def to_sina(symbol: str) -> str:
    """510050.SH → sh510050, 159915.SZ → sz159915"""
    code, exchange = symbol.split(".")
    prefix = "sh" if exchange == "SH" else "sz"
    return f"{prefix}{code}"


def get_existing(cur, symbol: str) -> set:
    cur.execute(
        "SELECT DISTINCT timestamp::date FROM ohlc "
        "WHERE symbol = %s AND data_source = 'akshare' AND timeframe = '1d'",
        (symbol,),
    )
    return {r[0] for r in cur.fetchall()}


def fetch_etf(sina_symbol: str) -> list[dict]:
    """Fetch full ETF history via Sina."""
    df = ak.fund_etf_hist_sina(symbol=sina_symbol)
    if df is None or len(df) == 0:
        return []

    records = []
    for _, row in df.iterrows():
        d = row["date"]
        if isinstance(d, (date, datetime)):
            d = d.strftime("%Y-%m-%d")
        else:
            d = str(d)
        records.append({
            "date": d,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "amount": float(row.get("amount", 0) or 0),
        })
    return records


def upsert(cur, symbol: str, records: list[dict]) -> int:
    count = 0
    for r in records:
        cur.execute("""
            INSERT INTO ohlc (symbol, data_source, timeframe, timestamp,
                              open, high, low, close, volume, backward_factor, data)
            VALUES (%s, 'akshare', '1d', %s::date, %s, %s, %s, %s, %s, 1.0, %s)
            ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                open = EXCLUDED.open, high = EXCLUDED.high,
                low = EXCLUDED.low, close = EXCLUDED.close,
                volume = EXCLUDED.volume, backward_factor = EXCLUDED.backward_factor,
                data = EXCLUDED.data
        """, (
            symbol, r["date"],
            r["open"], r["high"], r["low"], r["close"], r["volume"],
            json.dumps({"amount": r["amount"], "source": "akshare"}),
        ))
        count += 1
    return count


def main():
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()

    etfs = sorted(set(ETF_TOP100))
    logger.info(f"ETFs to fetch: {len(etfs)}")

    total_upserted = 0
    success = 0
    failed = 0

    for i, symbol in enumerate(etfs):
        sina_sym = to_sina(symbol)
        logger.info(f"[{i+1}/{len(etfs)}] ETF {symbol} → {sina_sym}")

        try:
            existing = get_existing(cur, symbol)
            records = fetch_etf(sina_sym)

            if not records:
                logger.warning(f"  ⚠️  no data (skipped)")
                failed += 1
            else:
                new_records = [r for r in records if r["date"] not in existing]
                if new_records:
                    count = upsert(cur, symbol, new_records)
                    conn.commit()
                    total_upserted += count
                    logger.info(f"  ✅ {len(new_records)} new ({count} upserted)")
                else:
                    logger.info(f"  ⏭  up to date ({len(existing)} existing)")
                success += 1
        except Exception as e:
            logger.error(f"  ❌ {e}")
            conn.rollback()
            failed += 1

        if i < len(etfs) - 1:
            time.sleep(DELAY)

    cur.close()
    conn.close()
    logger.info(f"Done. {success} success, {failed} failed, {total_upserted} records")


if __name__ == "__main__":
    main()
