#!/usr/bin/env python3
"""Fetch missing historical data - simplified version."""
import json
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
import tushare as ts
from farseer.config import settings



def get_incomplete():
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, MIN(timestamp::date) as first_date
        FROM ohlc
        WHERE symbol NOT LIKE '15%' AND symbol NOT LIKE '51%' AND symbol NOT LIKE '58%'
        GROUP BY symbol
        HAVING MIN(timestamp::date) > '2000-01-01'
          AND COUNT(*) < 7000
        ORDER BY first_date
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def fetch_before(symbol, before_date):
    """Fetch data before given date."""
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    # Get first backward_factor
    cur.execute(
        "SELECT backward_factor FROM ohlc WHERE symbol = %s ORDER BY timestamp ASC LIMIT 1",
        (symbol,)
    )
    row = cur.fetchone()
    first_factor = float(row[0]) if row else 1.0
    
    end_date = (before_date - timedelta(days=1)).strftime("%Y%m%d")
    
    time.sleep(0.8)
    df = ts.pro_bar(ts_code=symbol, start_date="19900101", end_date=end_date, adj="hfq")
    
    if df is None or len(df) == 0:
        cur.close()
        conn.close()
        return 0
    
    # Get adj_factors
    time.sleep(0.8)
    df_adj = pro.adj_factor(ts_code=symbol, start_date="19900101", end_date=end_date)
    
    count = 0
    for _, row in df.iterrows():
        trade_date = row['trade_date']
        date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        
        adj_val = 1.0
        if df_adj is not None and len(df_adj) > 0:
            adj_rows = df_adj[df_adj['trade_date'] == trade_date]
            if len(adj_rows) > 0:
                adj_val = float(adj_rows.iloc[0]['adj_factor'])
        
        backward_factor = adj_val / first_factor if first_factor > 0 else 1.0
        
        cur.execute("""
            INSERT INTO ohlc (symbol, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
            VALUES (%s, '1d', %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                close = EXCLUDED.close, volume = EXCLUDED.volume,
                backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
        """, (
            symbol, date_str,
            float(row['open']), float(row['high']), float(row['low']), float(row['close']),
            int(float(row.get('vol', 0))), backward_factor,
            json.dumps({"amount": float(row.get('amount', 0)) * 1000, "source": "tushare"})
        ))
        count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return count


def main():
    symbols = get_incomplete()
    logging.info(f"Found {len(symbols)} symbols to process")
    
    total = 0
    for i, (symbol, first_date) in enumerate(symbols):
        logging.info(f"[{i+1}/{len(symbols)}] {symbol}: DB starts {first_date}")
        added = fetch_before(symbol, first_date)
        if added > 0:
            logging.info(f"  Added {added} records")
            total += added
        else:
            logging.info(f"  No earlier data")
    
    logging.info(f"Done! Added {total} total records")


if __name__ == "__main__":
    main()
