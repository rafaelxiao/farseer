#!/usr/bin/env python3
"""
Fetch missing historical data for stocks that hit the 5000 bar limit.
Splits date ranges to get full history from IPO.
"""
import json
import logging
import time
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
import tushare as ts
from farseer.config import settings



def get_incomplete_symbols():
    """Find stocks missing historical data."""
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT symbol, MIN(timestamp::date) as first_date, COUNT(*) as records
        FROM ohlc
        WHERE symbol NOT LIKE '15%' AND symbol NOT LIKE '51%' AND symbol NOT LIKE '58%'
        GROUP BY symbol
        HAVING MIN(timestamp::date) > '2000-01-01'
        ORDER BY first_date
    """)
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def check_ipo_date(symbol):
    """Get IPO date from tushare."""
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    df = pro.stock_basic(ts_code=symbol, fields="ts_code,list_date")
    if len(df) > 0:
        return df.iloc[0]['list_date']
    return None


def fetch_missing_history(symbol, existing_first_date):
    """Fetch history before existing_first_date."""
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    # Get first backward_factor for normalization
    cur.execute(
        "SELECT backward_factor FROM ohlc WHERE symbol = %s ORDER BY timestamp ASC LIMIT 1",
        (symbol,)
    )
    first_row = cur.fetchone()
    first_factor = float(first_row[0]) if first_row else 1.0
    
    # Fetch in chunks going backwards
    end_date = (existing_first_date - timedelta(days=1)).strftime("%Y%m%d")
    start_date = "19900101"
    
    total_added = 0
    current_end = end_date
    
    while True:
        time.sleep(0.8)
        
        df = ts.pro_bar(
            ts_code=symbol,
            start_date=start_date,
            end_date=current_end,
            adj="hfq"
        )
        
        if df is None or len(df) == 0:
            break
        
        # Get adj_factors
        time.sleep(0.8)
        df_adj = pro.adj_factor(ts_code=symbol, start_date=start_date, end_date=current_end)
        
        # Insert records
        for _, row in df.iterrows():
            trade_date = row['trade_date']
            date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
            
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
                float(row['open']), float(row['high']), float(row['low']), float(row['close']),
                int(float(row.get('vol', 0))), backward_factor,
                json.dumps({"amount": float(row.get('amount', 0)) * 1000, "source": "tushare"})
            ))
            total_added += 1
        
        conn.commit()
        
        # Check if we got all data
        if len(df) < 5000:
            break
        
        # Move to earlier period
        earliest = df['trade_date'].min()
        if earliest <= start_date:
            break
        current_end = (datetime.strptime(earliest, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
    
    cur.close()
    conn.close()
    return total_added


def main():
    symbols = get_incomplete_symbols()
    logging.info(f"Found {len(symbols)} stocks with potentially incomplete history")
    
    total_added = 0
    fixed = 0
    
    for symbol, first_date, records in symbols:
        # Check IPO date
        ipo = check_ipo_date(symbol)
        if not ipo:
            continue
        
        ipo_date = datetime.strptime(ipo, "%Y%m%d").date()
        db_first = first_date
        
        # Skip if DB already starts close to IPO
        if (db_first - ipo_date).days < 30:
            continue
        
        logging.info(f"{symbol}: IPO={ipo}, DB starts={first_date}, missing {(db_first - ipo_date).days} days")
        
        added = fetch_missing_history(symbol, db_first)
        if added > 0:
            logging.info(f"  Added {added} records")
            total_added += added
            fixed += 1
        
        time.sleep(2)  # Rate limit between symbols
    
    logging.info(f"Done! Fixed {fixed} symbols, added {total_added} total records")


if __name__ == "__main__":
    main()
