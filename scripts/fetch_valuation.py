#!/usr/bin/env python3
"""Fetch valuation metrics (PE, PB, PS) for all symbols."""
import asyncio
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

def fetch_valuation(symbol):
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    ts_code = symbol
    
    time.sleep(0.3)
    df = pro.daily_basic(ts_code=ts_code, fields="ts_code,trade_date,pe,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_mv")
    
    if df is None or len(df) == 0:
        return 0
    
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    
    count = 0
    for _, row in df.head(1).iterrows():  # Just latest
        trade_date = row.get('trade_date')
        if not trade_date:
            continue
        
        date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
        
        data = {
            "pe": float(row['pe']) if row.get('pe') and not math.isnan(row['pe']) else None,
            "pb": float(row['pb']) if row.get('pb') and not math.isnan(row['pb']) else None,
            "ps": float(row['ps']) if row.get('ps') and not math.isnan(row['ps']) else None,
            "ps_ttm": float(row['ps_ttm']) if row.get('ps_ttm') and not math.isnan(row['ps_ttm']) else None,
            "dividend_yield": float(row['dv_ttm']) if row.get('dv_ttm') and not math.isnan(row['dv_ttm']) else None,
            "market_cap": float(row['total_mv']) if row.get('total_mv') and not math.isnan(row['total_mv']) else None,
        }
        data = {k: v for k, v in data.items() if v is not None}
        
        if data:
            cur.execute("""
                INSERT INTO fundamentals (symbol, date, category, data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol, date, category) DO UPDATE SET data = %s
            """, (symbol, date, 'valuation', json.dumps(data), json.dumps(data)))
            count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return count

async def main():
    symbols = get_stock_symbols()
    logging.info(f"Fetching valuation for {len(symbols)} symbols")
    
    success = 0
    for i, symbol in enumerate(symbols):
        try:
            count = fetch_valuation(symbol)
            success += 1
            if (i + 1) % 100 == 0:
                logging.info(f"[{i+1}/{len(symbols)}] {success} success")
        except Exception as e:
            logging.error(f"Failed {symbol}: {e}")
    
    logging.info(f"Done! {success} success")

if __name__ == "__main__":
    asyncio.run(main())
