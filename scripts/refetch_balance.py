#!/usr/bin/env python3
"""Re-fetch balance sheet data."""
import json
import logging
import math
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
import tushare as ts
from farseer.config import settings


def get_stock_symbols():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT symbol FROM fundamentals 
        WHERE category = 'income' 
        AND symbol NOT LIKE '160%' AND symbol NOT LIKE '501%' 
        AND symbol NOT LIKE '551%' AND symbol NOT LIKE '520%'
    """)
    symbols = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return symbols

def fetch_balance(symbol):
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    ts_code = symbol
    
    time.sleep(0.5)
    df = pro.balancesheet(ts_code=ts_code, fields="ts_code,end_date,total_assets,total_cur_assets,total_nca,total_liab,total_cur_liab,total_ncl,total_hldr_eqy_exc_min_int")
    
    if df is None or len(df) == 0:
        return 0
    
    # Remove duplicates (keep latest announcement)
    df = df.drop_duplicates(subset=['end_date'], keep='first')
    
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    
    count = 0
    for _, row in df.head(8).iterrows():
        period = row.get('end_date')
        if not period:
            continue
        
        date = f"{period[:4]}-{period[4:6]}-{period[6:8]}"
        
        data = {
            "total_assets": float(row['total_assets']) if row.get('total_assets') and not math.isnan(row['total_assets']) else None,
            "total_cur_assets": float(row['total_cur_assets']) if row.get('total_cur_assets') and not math.isnan(row['total_cur_assets']) else None,
            "total_liab": float(row['total_liab']) if row.get('total_liab') and not math.isnan(row['total_liab']) else None,
            "total_cur_liab": float(row['total_cur_liab']) if row.get('total_cur_liab') and not math.isnan(row['total_cur_liab']) else None,
            "equity": float(row['total_hldr_eqy_exc_min_int']) if row.get('total_hldr_eqy_exc_min_int') and not math.isnan(row['total_hldr_eqy_exc_min_int']) else None,
        }
        data = {k: v for k, v in data.items() if v is not None}
        
        if data:
            cur.execute("""
                INSERT INTO fundamentals (symbol, date, category, data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol, date, category) DO UPDATE SET data = %s
            """, (symbol, date, 'balance_sheet', json.dumps(data), json.dumps(data)))
            count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return count

# Run for 000001.SZ first
logging.info("Re-fetching balance sheet for 000001.SZ...")
count = fetch_balance("000001.SZ")
logging.info(f"Done: {count} periods")
