"""
Daily fetch job - updates OHLC and fundamentals data.
"""

import json
import logging
import math
import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from farseer.universe.sets import CSI300, CSI500, ETF_TOP100, INDICES

logger = logging.getLogger(__name__)


# Chinese market holidays (2026) - update annually
MARKET_HOLIDAYS_2026 = [
    # New Year
    "2026-01-01", "2026-01-02",
    # Spring Festival
    "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-21", "2026-02-22", "2026-02-23",
    # Qingming
    "2026-04-04", "2026-04-05", "2026-04-06",
    # Labor Day
    "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",
    # Dragon Boat
    "2026-06-19", "2026-06-20", "2026-06-21",
    # Mid-Autumn & National Day
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-07",
]


def is_market_closed() -> bool:
    """Check if market is closed (weekend or holiday)."""
    today = datetime.now()
    
    # Check weekend
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        logger.info(f"Market closed: weekend ({today.strftime('%A')})")
        return True
    
    # Check holiday
    today_str = today.strftime("%Y-%m-%d")
    if today_str in MARKET_HOLIDAYS_2026:
        logger.info(f"Market closed: holiday ({today_str})")
        return True
    
    return False


def get_all_symbols() -> list[str]:
    """Get all symbols from universe sets (deduplicated)."""
    symbols = set()
    symbols.update(CSI300)
    symbols.update(CSI500)
    symbols.update(ETF_TOP100)
    return sorted(symbols)


def split_by_type(symbols: list[str]) -> tuple[list[str], list[str]]:
    """Split symbols into stocks and ETFs."""
    from farseer.symbols.utils import is_etf
    stocks = [s for s in symbols if not is_etf(s)]
    etfs = [s for s in symbols if is_etf(s)]
    return stocks, etfs


def _log_task_start(conn, cur) -> int:
    """Log task start and return task_id."""
    cur.execute(
        "INSERT INTO task_runs (job_id, status, started_at) VALUES (%s, %s, now()) RETURNING id",
        ("daily_fetch", "running")
    )
    task_id = cur.fetchone()[0]
    conn.commit()
    return task_id


def _log_task_skip(conn, cur):
    """Log skipped task."""
    cur.execute(
        "INSERT INTO task_runs (job_id, status, started_at, finished_at, result) VALUES (%s, %s, now(), now(), %s)",
        ("daily_fetch", "skipped", '{"status": "skipped", "reason": "market closed"}')
    )
    conn.commit()


def _log_task_result(conn, cur, task_id: int, status: str, result: dict):
    """Log task completion."""
    cur.execute(
        "UPDATE task_runs SET status = %s, finished_at = now(), result = %s WHERE id = %s",
        (status, json.dumps(result), task_id)
    )
    conn.commit()


def fetch_ohlc(pro, conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch OHLC data for symbols. Returns (success, failed)."""
    logger.info(f"=== Fetching OHLC data (last 3 days) for {len(symbols)} symbols ===")
    
    from farseer.symbols.utils import is_etf
    
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=4)).strftime("%Y%m%d")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            time.sleep(0.4)
            
            if is_etf(symbol):
                # ETF: fetch actual prices from fund_daily
                df = pro.fund_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    # Get existing backward_factor
                    cur.execute("SELECT backward_factor FROM ohlc WHERE symbol=%s AND data_source='tushare' ORDER BY timestamp DESC LIMIT 1", (symbol,))
                    first_row = cur.fetchone()
                    bf = float(first_row[0]) if first_row else 1.0
                    
                    for _, row in df.iterrows():
                        trade_date = row['trade_date']
                        date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                        cur.execute("""
                            INSERT INTO ohlc (symbol, data_source, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
                            VALUES (%s, 'tushare', '1d', %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                                close = EXCLUDED.close, volume = EXCLUDED.volume,
                                backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                        """, (symbol, date_str, float(row['open']), float(row['high']),
                              float(row['low']), float(row['close']), int(float(row.get('vol', 0))),
                              bf, json.dumps({"amount": float(row.get('amount', 0)) * 1000, "source": "tushare"})))
                    conn.commit()
                    success += 1
                else:
                    failed += 1
            else:
                # Stock: fetch actual prices, store as 后复权
                df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
                if df is not None and len(df) > 0:
                    time.sleep(0.3)
                    df_adj = pro.adj_factor(ts_code=symbol, start_date=start_date, end_date=end_date)
                    
                    cur.execute("SELECT backward_factor FROM ohlc WHERE symbol=%s AND data_source='tushare' ORDER BY timestamp ASC LIMIT 1", (symbol,))
                    first_row = cur.fetchone()
                    first_factor = float(first_row[0]) if first_row else 1.0
                    
                    for _, row in df.iterrows():
                        trade_date = row['trade_date']
                        date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                        adj_val = 1.0
                        if df_adj is not None and len(df_adj) > 0:
                            adj_row = df_adj[df_adj['trade_date'] == trade_date]
                            if len(adj_row) > 0:
                                adj_val = float(adj_row.iloc[0]['adj_factor'])
                        backward_factor = adj_val / first_factor if first_factor > 0 else 1.0
                        bf = backward_factor
                        cur.execute("""
                            INSERT INTO ohlc (symbol, data_source, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
                            VALUES (%s, 'tushare', '1d', %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                                close = EXCLUDED.close, volume = EXCLUDED.volume,
                                backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                        """, (symbol, date_str,
                              float(row['open'])*bf, float(row['high'])*bf,
                              float(row['low'])*bf, float(row['close'])*bf,
                              int(float(row.get('vol', 0))), bf,
                              json.dumps({"amount": float(row.get('amount', 0)) * 1000, "source": "tushare"})))
                    conn.commit()
                    success += 1
                else:
                    failed += 1
        except Exception as e:
            logger.error(f"OHLC failed {symbol}: {e}")
            failed += 1
            conn.rollback()
    
    logger.info(f"OHLC complete: {success} success, {failed} failed")
    return success, failed


def fetch_index_ohlc(pro, conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch index OHLC data. No adjustment factors — simpler than stocks."""
    logger.info(f"=== Fetching Index OHLC for {len(symbols)} indices ===")
    
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=4)).strftime("%Y%m%d")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            time.sleep(0.4)
            df = pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            
            if df is not None and len(df) > 0:
                for _, row in df.iterrows():
                    trade_date = row['trade_date']
                    date_str = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}"
                    cur.execute("""
                        INSERT INTO ohlc (symbol, data_source, timeframe, timestamp, open, high, low, close, volume, backward_factor, data)
                        VALUES (%s, 'tushare', '1d', %s, %s, %s, %s, %s, %s, 1.0, %s)
                        ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                            open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                            close = EXCLUDED.close, volume = EXCLUDED.volume,
                            backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                    """, (symbol, date_str, float(row['open']), float(row['high']),
                          float(row['low']), float(row['close']), int(float(row.get('vol', 0))),
                          json.dumps({"amount": float(row.get('amount', 0)), "source": "tushare"})))
                conn.commit()
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Index failed {symbol}: {e}")
            failed += 1
            conn.rollback()
    
    logger.info(f"Index OHLC complete: {success} success, {failed} failed")
    return success, failed


def fetch_stock_fundamentals(pro, conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch fundamentals for stock symbols. Returns (success, failed)."""
    logger.info(f"=== Fetching Stock Fundamentals for {len(symbols)} symbols ===")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            time.sleep(0.5)
            
            # Income
            df_income = pro.income(ts_code=symbol, fields="ts_code,end_date,revenue,n_income_attr_p,basic_eps,diluted_eps")
            if df_income is not None and len(df_income) > 0:
                for _, row in df_income.head(4).iterrows():
                    period = row.get('end_date')
                    if period:
                        date = f"{period[:4]}-{period[4:6]}-{period[6:8]}"
                        data = {
                            "revenue": float(row['revenue']) if row.get('revenue') else None,
                            "net_income_attr_p": float(row['n_income_attr_p']) if row.get('n_income_attr_p') else None,
                            "basic_eps": float(row['basic_eps']) if row.get('basic_eps') else None,
                            "diluted_eps": float(row['diluted_eps']) if row.get('diluted_eps') else None,
                        }
                        data = {k: v for k, v in data.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}
                        if data:
                            cur.execute("""
                                INSERT INTO fundamentals (symbol, date, category, data)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (symbol, date, category) DO UPDATE SET data = %s
                            """, (symbol, date, 'income', json.dumps(data), json.dumps(data)))
            
            # Financial indicators
            time.sleep(0.5)
            df_fina = pro.fina_indicator(ts_code=symbol, fields="ts_code,end_date,eps,roe,roa,roa_yearly,netprofit_margin,debt_to_assets,op_yoy,netprofit_yoy,bps")
            if df_fina is not None and len(df_fina) > 0:
                for _, row in df_fina.head(4).iterrows():
                    period = row.get('end_date')
                    if period:
                        date = f"{period[:4]}-{period[4:6]}-{period[6:8]}"
                        roa = row.get('roa')
                        roa_yearly = row.get('roa_yearly')
                        data = {
                            "eps": float(row['eps']) if row.get('eps') and not math.isnan(row['eps']) else None,
                            "roe": float(row['roe']) if row.get('roe') and not math.isnan(row['roe']) else None,
                            "roa": float(roa or roa_yearly) if (roa and not math.isnan(roa)) or (roa_yearly and not math.isnan(roa_yearly)) else None,
                            "net_margin": float(row['netprofit_margin']) if row.get('netprofit_margin') and not math.isnan(row['netprofit_margin']) else None,
                            "debt_to_assets": float(row['debt_to_assets']) if row.get('debt_to_assets') and not math.isnan(row['debt_to_assets']) else None,
                            "revenue_yoy": float(row['op_yoy']) if row.get('op_yoy') and not math.isnan(row['op_yoy']) else None,
                            "net_income_yoy": float(row['netprofit_yoy']) if row.get('netprofit_yoy') and not math.isnan(row['netprofit_yoy']) else None,
                            "bps": float(row['bps']) if row.get('bps') and not math.isnan(row['bps']) else None,
                        }
                        data = {k: v for k, v in data.items() if v is not None}
                        if data:
                            cur.execute("""
                                INSERT INTO fundamentals (symbol, date, category, data)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (symbol, date, category) DO UPDATE SET data = %s
                            """, (symbol, date, 'financial_indicator', json.dumps(data), json.dumps(data)))
            
            conn.commit()
            success += 1
            
        except Exception as e:
            logger.error(f"Fundamentals failed {symbol}: {e}")
            failed += 1
            conn.rollback()
    
    logger.info(f"Stock fundamentals complete: {success} success, {failed} failed")
    return success, failed


def fetch_etf_fundamentals(pro, conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch fundamentals for ETF symbols. Returns (success, failed)."""
    logger.info(f"=== Fetching ETF Stats for {len(symbols)} symbols ===")
    
    success = 0
    failed = 0
    
    for symbol in symbols:
        try:
            time.sleep(0.5)
            
            # ETF NAV
            df_nav = pro.fund_nav(ts_code=symbol, fields="ts_code,nav_date,unit_nav,accum_nav")
            if df_nav is not None and len(df_nav) > 0:
                latest = df_nav.iloc[0]
                nav_data = {
                    "unit_nav": float(latest['unit_nav']) if latest.get('unit_nav') else None,
                    "accum_nav": float(latest['accum_nav']) if latest.get('accum_nav') else None,
                }
                nav_data = {k: v for k, v in nav_data.items() if v is not None}
                if nav_data:
                    nav_date = latest.get('nav_date', '')
                    if nav_date:
                        date = f"{nav_date[:4]}-{nav_date[4:6]}-{nav_date[6:8]}"
                        cur.execute("""
                            INSERT INTO fundamentals (symbol, data_source, date, category, data)
                            VALUES (%s, 'tushare', %s, %s, %s)
                            ON CONFLICT (symbol, data_source, date, category) DO UPDATE SET data = %s
                        """, (symbol, date, 'etf_nav', json.dumps(nav_data), json.dumps(nav_data)))
            
            conn.commit()
            success += 1
            
        except Exception as e:
            logger.error(f"ETF failed {symbol}: {e}")
            failed += 1
            conn.rollback()
    
    logger.info(f"ETF stats complete: {success} success, {failed} failed")
    return success, failed


def _validate_token(pro) -> bool:
    """Check if Tushare token is valid."""
    try:
        df = pro.daily(ts_code="000001.SZ", start_date="20260601", end_date="20260617")
        return df is not None and len(df) > 0
    except Exception as e:
        logger.error(f"Tushare token validation failed: {e}")
        return False


def daily_fetch_job():
    """Daily fetch: update all universe symbols with latest data."""
    import tushare as ts
    import psycopg2
    from farseer.config import settings
    
    logger.info("Daily fetch job starting...")
    
    # Check if market is open today
    if is_market_closed():
        logger.info("Skipping fetch - market is closed")
        conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
        cur = conn.cursor()
        _log_task_skip(conn, cur)
        cur.close()
        conn.close()
        return
    
    # Setup tushare
    from farseer.utils.tushare import get_tushare_pro
    pro = get_tushare_pro()
    
    # Validate token first
    if not _validate_token(pro):
        logger.error("Tushare token is invalid. All fetches will fail.")
        conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
        cur = conn.cursor()
        task_id = _log_task_start(conn, cur)
        _log_task_result(conn, cur, task_id, "failed", {
            "error": "Tushare token invalid/expired. Update TUSHARE_TOKEN in .env"
        })
        cur.close()
        conn.close()
        return
    
    # Connect to DB
    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    
    # Log task start
    task_id = _log_task_start(conn, cur)
    
    try:
        # Get all symbols
        symbols = get_all_symbols()
        stock_symbols, etf_symbols = split_by_type(symbols)
        logger.info(f"Daily fetch: {len(stock_symbols)} stocks, {len(etf_symbols)} ETFs")
        
        # Fetch OHLC
        ohlc_success, ohlc_failed = fetch_ohlc(pro, conn, cur, symbols)
        
        # Fetch Index OHLC
        idx_success, idx_failed = fetch_index_ohlc(pro, conn, cur, INDICES)
        
        # Fetch Stock Fundamentals
        fund_success, fund_failed = fetch_stock_fundamentals(pro, conn, cur, stock_symbols)
        
        # Fetch ETF Fundamentals
        etf_success, etf_failed = fetch_etf_fundamentals(pro, conn, cur, etf_symbols)
        
        # Log success
        result = {
            "ohlc": {"success": ohlc_success, "failed": ohlc_failed},
            "index": {"success": idx_success, "failed": idx_failed},
            "fundamentals": {"success": fund_success, "failed": fund_failed},
            "etf": {"success": etf_success, "failed": etf_failed},
        }
        _log_task_result(conn, cur, task_id, "success", result)
        
    except Exception as e:
        logger.exception("Daily fetch failed")
        _log_task_result(conn, cur, task_id, "failed", {"error": str(e)})
    finally:
        cur.close()
        conn.close()
    
    logger.info("Daily fetch job finished")


def register_jobs(scheduler: BackgroundScheduler):
    """Register scheduled jobs."""
    
    # Daily fetch: run at 18:00 (after China market close at 15:00)
    scheduler.add_job(
        daily_fetch_job,
        trigger=CronTrigger(hour=18, minute=0),
        id="daily_fetch",
        name="Daily Universe Fetch",
        replace_existing=True,
    )
    
    logger.info("Registered jobs: daily_fetch (18:00)")
