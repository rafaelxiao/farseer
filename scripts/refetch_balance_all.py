#!/usr/bin/env python3
import json, logging, math, time
from datetime import datetime
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
import psycopg2
import tushare as ts
from farseer.config import settings

def get_symbols():
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM fundamentals WHERE category = 'income' AND symbol NOT LIKE '160%' AND symbol NOT LIKE '501%' AND symbol NOT LIKE '551%' AND symbol NOT LIKE '520%'")
    symbols = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return symbols

def fetch(symbol):
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    time.sleep(0.5)
    df = pro.balancesheet(ts_code=symbol, fields="ts_code,end_date,total_assets,total_cur_assets,total_liab,total_cur_liab,total_hldr_eqy_exc_min_int")
    if df is None or len(df) == 0: return 0
    df = df.drop_duplicates(subset=['end_date'], keep='first')
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    count = 0
    for _, row in df.head(12).iterrows():
        period = row.get('end_date')
        if not period: continue
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
            cur.execute("INSERT INTO fundamentals (symbol, date, category, data) VALUES (%s,%s,%s,%s) ON CONFLICT (symbol, date, category) DO UPDATE SET data=%s", (symbol, date, 'balance_sheet', json.dumps(data), json.dumps(data)))
            count += 1
    conn.commit(); cur.close(); conn.close()
    return count

symbols = get_symbols()
logging.info(f"Re-fetching balance sheet for {len(symbols)} symbols")
success = 0
for i, sym in enumerate(symbols):
    try:
        fetch(sym); success += 1
        if (i+1) % 100 == 0: logging.info(f"[{i+1}/{len(symbols)}] {success} success")
    except Exception as e: logging.error(f"Failed {sym}: {e}")
logging.info(f"Done! {success} success")
