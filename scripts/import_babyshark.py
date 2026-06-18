#!/usr/bin/env python3
"""Import BabyShark minute data into Farseer OHLC table."""
import json
import duckdb
import psycopg2
from datetime import datetime
from farseer.config import settings

# Connect
babyshark = duckdb.connect('/home/ubuntu/projects/babyshark/.db/stock_data.db')
pg = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
pg.autocommit = True
cur = pg.cursor()

# Get total count
total = babyshark.execute("SELECT COUNT(*) FROM minute_hist_data").fetchone()[0]
print(f"Total rows: {total:,}")

batch_size = 5000
offset = 0
imported = 0
skipped = 0

while offset < total:
    rows = babyshark.execute(f"""
        SELECT code, date, time, open, high, low, close, volume, name
        FROM minute_hist_data ORDER BY date, time, code
        LIMIT {batch_size} OFFSET {offset}
    """).fetchall()

    if not rows:
        break

    values = []
    for code, dt, tm, o, h, l, c, v, name in rows:
        ts = datetime.combine(dt, tm)
        values.append((
            code, 'qmt', '1m', ts,
            float(o), float(h), float(l), float(c),
            int(v) if v else 0, 1.0,
            json.dumps({"name": name, "source": "qmt"}),
        ))

    # Batch upsert
    from psycopg2.extras import execute_values
    execute_values(cur, """
        INSERT INTO ohlc (symbol, data_source, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
        VALUES %s
        ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
            open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
            close = EXCLUDED.close, volume = EXCLUDED.volume,
            backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
    """, values, template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

    imported += len(rows)
    offset += len(rows)
    print(f"  {imported:,}/{total:,} ({imported*100//total}%)")

print(f"\nDone: {imported:,} rows")

# Verify
cur.execute("SELECT COUNT(*) FROM ohlc WHERE data_source='qmt'")
qmt = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM ohlc WHERE data_source='qmt' AND timeframe='1m'")
min_cnt = cur.fetchone()[0]
print(f"QMT total: {qmt:,}, minute: {min_cnt:,}")

cur.close()
pg.close()
babyshark.close()
