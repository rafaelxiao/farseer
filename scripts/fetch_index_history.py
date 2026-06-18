#!/usr/bin/env python3
"""Fetch full index history and upsert to OHLC table."""
import json, time, psycopg2
from farseer.utils.tushare import get_tushare_pro
from farseer.config import settings
from farseer.universe.sets import INDICES

pro = get_tushare_pro()
conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2",""))
conn.autocommit = True
cur = conn.cursor()

print(f"Fetching {len(INDICES)} indices: {INDICES}\n")

total = 0
for symbol in INDICES:
    try:
        time.sleep(0.4)
        df = pro.index_daily(ts_code=symbol, start_date='19900101', end_date='20260618')
        if df is None or len(df) == 0:
            print(f"  {symbol}: no data")
            continue
        
        n = 0
        for _, row in df.iterrows():
            td = row['trade_date']
            date_str = f"{td[:4]}-{td[4:6]}-{td[6:8]}"
            cur.execute("""
                INSERT INTO ohlc (symbol, data_source, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
                VALUES (%s, 'tushare', '1d', %s, %s, %s, %s, %s, %s, 1.0, %s)
                ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                    open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                    close=EXCLUDED.close, volume=EXCLUDED.volume,
                    backward_factor=EXCLUDED.backward_factor, data=EXCLUDED.data
            """, (symbol, date_str, float(row['open']), float(row['high']),
                  float(row['low']), float(row['close']), int(float(row.get('vol', 0))),
                  json.dumps({"amount": float(row.get('amount', 0)), "source": "tushare"})))
            n += 1
        
        total += n
        print(f"  {symbol}: {n:,} bars")
    except Exception as e:
        print(f"  {symbol}: FAILED - {e}")

print(f"\nDone: {total:,} total bars")
cur.execute("SELECT COUNT(*) FROM ohlc WHERE data_source='tushare' AND symbol IN %s", (tuple(INDICES),))
print(f"DB count: {cur.fetchone()[0]:,}")
cur.close(); conn.close()
