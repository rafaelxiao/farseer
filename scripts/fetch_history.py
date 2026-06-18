#!/usr/bin/env python3
"""
Fetch missing historical data for symbols that hit the 5000 bar limit.
Splits the date range to get full history.
"""
import json
import logging
import math
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
import tushare as ts
from farseer.config import settings



def get_incomplete_symbols():
    """Find symbols that might have incomplete history."""
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    cur.execute("""
        WITH stock_dates AS (
            SELECT 
                symbol,
                COUNT(*) as records,
                MIN(timestamp::date) as first_date
            FROM ohlc
            GROUP BY symbol
        )
        SELECT symbol, records, first_date
        FROM stock_dates
        WHERE first_date <= '2005-01-01'  -- Early listed stocks
          AND records < 5500  -- Should have more records
        ORDER BY first_date
    """)
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def fetch_full_history(symbol):
    """Fetch full history by splitting date range."""
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    ts_code = symbol
    
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    # Get existing first date
    cur.execute(
        "SELECT MIN(timestamp::date) FROM ohlc WHERE symbol = %s",
        (symbol,)
    )
    existing_first = cur.fetchone()[0]
    
    if not existing_first:
        cur.close()
        conn.close()
        return 0
    
    # Fetch data before existing first date
    end_date = (existing_first - timedelta(days=1)).strftime("%Y%m%d")
    start_date = "19900101"
    
    logging.info(f"Fetching {symbol} from {start_date} to {end_date}")
    
    # Fetch in chunks to avoid 5000 limit
    all_records = []
    current_end = end_date
    
    while current_end > start_date:
        time.sleep(0.6)  # Rate limit
        
        # Fetch 后复权
        df = ts.pro_bar(
            ts_code=ts_code,
            start_date=start_date,
            end_date=current_end,
            adj="hfq"
        )
        
        if df is None or len(df) == 0:
            break
        
        all_records.extend(df.to_dict('records'))
        
        # Move to earlier period
        earliest = df['trade_date'].min()
        if earliest <= start_date:
            break
        current_end = (datetime.strptime(earliest, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
        
        if len(df) < 5000:
            break  # Got all data
    
    if not all_records:
        cur.close()
        conn.close()
        return 0
    
    # Get adj_factor for normalization
    time.sleep(0.6)
    df_adj = pro.adj_factor(ts_code=ts_code, start_date=start_date, end_date=end_date)
    
    # Get first adj_factor from existing data for normalization
    cur.execute(
        "SELECT backward_factor FROM ohlc WHERE symbol = %s ORDER BY timestamp ASC LIMIT 1",
        (symbol,)
    )
    first_row = cur.fetchone()
    first_factor = float(first_row[0]) if first_row else 1.0
    
    # Insert records
    count = 0
    for record in all_records:
        trade_date = record['trade_date']
        date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        
        # Get adj_factor for this date
        adj_val = 1.0
        if df_adj is not None and len(df_adj) > 0:
            adj_row = df_adj[df_adj['trade_date'] == trade_date]
            if len(adj_row) > 0:
                adj_val = float(adj_row.iloc[0]['adj_factor'])
        
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
            float(record['open']), float(record['high']), float(record['low']), float(record['close']),
            int(float(record.get('vol', 0))), backward_factor,
            json.dumps({"amount": float(record.get('amount', 0)) * 1000, "source": "tushare"})
        ))
        count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return count


def main():
    symbols = get_incomplete_symbols()
    logging.info(f"Found {len(symbols)} symbols with potentially incomplete history")
    
    total_added = 0
    for symbol, records, first_date in symbols:
        logging.info(f"Processing {symbol}: {records} records, first={first_date}")
        added = fetch_full_history(symbol)
        if added > 0:
            logging.info(f"  Added {added} historical records")
            total_added += added
        else:
            logging.info(f"  No additional history found")
    
    logging.info(f"Done! Added {total_added} total historical records")


if __name__ == "__main__":
    main()
