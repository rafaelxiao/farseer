#!/usr/bin/env python3
"""Re-fetch financial indicators for all symbols."""
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

import psycopg2
import tushare as ts
from farseer.config import settings


def get_symbols():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT symbol FROM fundamentals 
        WHERE category = 'income' AND symbol NOT LIKE '160%' AND symbol NOT LIKE '501%' 
        AND symbol NOT LIKE '551%' AND symbol NOT LIKE '520%'
    """)
    symbols = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return symbols

def fetch_and_store(symbol):
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    ts_code = symbol
    
    # Fetch financial indicators
    time.sleep(0.6)
    df = pro.fina_indicator(ts_code=ts_code, fields="ts_code,end_date,eps,roe,roe_dt,roa,roa_yearly,netprofit_margin,grossprofit_margin,debt_to_assets,op_yoy,n_income_yoy,bps")
    
    if df is None or len(df) == 0:
        return 0
    
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/farseer")
    cur = conn.cursor()
    
    count = 0
    for _, row in df.head(12).iterrows():
        period = row.get('end_date')
        if not period:
            continue
        
        date = f"{period[:4]}-{period[4:6]}-{period[6:8]}"
        
        roa = row.get('roa')
        roa_yearly = row.get('roa_yearly')
        roa_val = float(roa or roa_yearly) if roa or roa_yearly else None
        
        data = {
            "eps": float(row['eps']) if row.get('eps') else None,
            "roe": float(row['roe']) if row.get('roe') else None,
            "roe_dt": float(row['roe_dt']) if row.get('roe_dt') else None,
            "roa": roa_val,
            "net_margin": float(row['netprofit_margin']) if row.get('netprofit_margin') else None,
            "gross_margin": float(row['grossprofit_margin']) if row.get('grossprofit_margin') else None,
            "debt_to_assets": float(row['debt_to_assets']) if row.get('debt_to_assets') else None,
            "revenue_yoy": float(row['op_yoy']) if row.get('op_yoy') else None,
            "net_income_yoy": float(row['n_income_yoy']) if row.get('n_income_yoy') else None,
            "bps": float(row['bps']) if row.get('bps') else None,
        }
        # Remove None
        data = {k: v for k, v in data.items() if v is not None}
        
        if data:
            import json
            cur.execute("""
                INSERT INTO fundamentals (symbol, date, category, data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol, date, category) DO UPDATE SET data = %s
            """, (symbol, date, 'financial_indicator', json.dumps(data), json.dumps(data)))
            count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return count

async def main():
    symbols = get_symbols()
    logging.info(f"Re-fetching indicators for {len(symbols)} symbols")
    
    success = 0
    failed = 0
    
    for i, symbol in enumerate(symbols):
        try:
            count = fetch_and_store(symbol)
            success += 1
            
            if (i + 1) % 100 == 0:
                logging.info(f"[{i+1}/{len(symbols)}] {success} success")
        except Exception as e:
            failed += 1
            logging.error(f"Failed {symbol}: {e}")
    
    logging.info(f"Done! {success} success, {failed} failed")

if __name__ == "__main__":
    asyncio.run(main())
