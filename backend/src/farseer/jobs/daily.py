"""
Daily fetch job - updates OHLC, fundamentals, and macro data.
"""

import json
import logging
import time
from datetime import date, datetime, timedelta

import akshare as ak
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from chinese_calendar import is_workday

from farseer.data.universe import CSI300, CSI500, ETF_TOP100, INDICES
from farseer.sources.akshare.macro import fetch_all_macro

logger = logging.getLogger(__name__)


def is_market_closed() -> bool:
    """Check if market is closed (weekend or Chinese holiday).
    Uses chinese-calendar which auto-updates each year."""
    today = date.today()
    if is_workday(today):
        return False
    logger.info(f"Market closed: {today} (weekend or holiday)")
    return True


def get_all_symbols() -> list[str]:
    """Get all symbols from universe sets (deduplicated)."""
    symbols = set()
    symbols.update(CSI300)
    symbols.update(CSI500)
    symbols.update(ETF_TOP100)
    return sorted(symbols)


def split_by_type(symbols: list[str]) -> tuple[list[str], list[str]]:
    """Split symbols into stocks and ETFs."""
    from farseer.data.universe import is_etf
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


def to_sina_symbol(symbol: str) -> str:
    """600519.SH → sh600519, 000858.SZ → sz000858"""
    code, exchange = symbol.split(".")
    prefix = "sh" if exchange == "SH" else "sz"
    return f"{prefix}{code}"


def _get_backward_factor(cur, symbol: str) -> float:
    """Get backward_factor for a symbol from existing DB rows."""
    cur.execute(
        "SELECT backward_factor FROM ohlc "
        "WHERE symbol=%s AND data_source='akshare' AND timeframe='1d' "
        "AND backward_factor != 1.0 ORDER BY timestamp DESC LIMIT 1",
        (symbol,),
    )
    row = cur.fetchone()
    if row:
        return float(row[0])
    return 1.0


# Index symbol mapping for stock_zh_index_daily
_INDEX_MAP = {
    "000001.SH": "sh000001", "000016.SH": "sh000016", "000300.SH": "sh000300",
    "000688.SH": "sh000688", "000852.SH": "sh000852", "000905.SH": "sh000905",
    "931566.SH": "sh931566", "931612.SH": "sh931612",
    "399001.SZ": "sz399001", "399005.SZ": "sz399005", "399006.SZ": "sz399006",
    "399673.SZ": "sz399673", "932000.SH": "sh932000", "931575.SH": "sh931575",
    "980017.SH": "sh980017",
}


def fetch_ohlc(conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch OHLC for stocks + ETFs via AKShare Sina. Returns (success, failed)."""
    from farseer.data.universe import is_etf
    logger.info(f"=== Fetching OHLC (AKShare) for {len(symbols)} symbols ===")

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=4)).strftime("%Y%m%d")

    success = 0
    failed = 0

    for i, symbol in enumerate(symbols):
        try:
            # Check latest existing date
            cur.execute(
                "SELECT MAX(timestamp) FROM ohlc "
                "WHERE symbol=%s AND data_source='akshare' AND timeframe='1d'",
                (symbol,),
            )
            latest = cur.fetchone()[0]
            latest_str = latest.strftime("%Y%m%d") if latest else "20000101"

            if latest_str >= end_date:
                # Already up to date — only log every 100th to avoid spam
                if i % 100 == 0:
                    logger.info(f"  [{i+1}/{len(symbols)}] {symbol}: up to date")
                success += 1
                continue

            sina_sym = to_sina_symbol(symbol)

            if is_etf(symbol):
                df = ak.fund_etf_hist_sina(symbol=sina_sym)
                bf = 1.0
                if df is not None and len(df) > 0:
                    records = []
                    for _, row in df.iterrows():
                        d = str(row["date"])
                        d_str = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 and "-" not in d else d[:10]
                        if d_str < start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:8]:
                            continue
                        records.append((d_str, float(row["open"]), float(row["high"]),
                                       float(row["low"]), float(row["close"]),
                                       int(row["volume"]), float(row.get("amount", 0) or 0)))
                    for r in records:
                        cur.execute("""
                            INSERT INTO ohlc (symbol, data_source, timeframe, timestamp,
                                              open, high, low, close, volume, backward_factor, data)
                            VALUES (%s, 'akshare', '1d', %s::date, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                                close = EXCLUDED.close, volume = EXCLUDED.volume,
                                backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                        """, (symbol, r[0], r[1], r[2], r[3], r[4], r[5],
                              bf, json.dumps({"amount": r[6], "source": "akshare"})))
            else:
                # Stock: fetch raw prices, store with backward_factor
                df = ak.stock_zh_a_daily(symbol=sina_sym, adjust="")
                if df is not None and len(df) > 0:
                    bf = _get_backward_factor(cur, symbol)
                    records = []
                    for _, row in df.iterrows():
                        d = str(row["date"])
                        if d < start_date:
                            continue
                        records.append((d, float(row["open"]), float(row["high"]),
                                       float(row["low"]), float(row["close"]),
                                       int(row["volume"]), float(row.get("amount", 0) or 0)))
                    for r in records:
                        cur.execute("""
                            INSERT INTO ohlc (symbol, data_source, timeframe, timestamp,
                                              open, high, low, close, volume, backward_factor, data)
                            VALUES (%s, 'akshare', '1d', %s::date, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                                close = EXCLUDED.close, volume = EXCLUDED.volume,
                                backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                        """, (symbol, r[0], r[1], r[2], r[3], r[4], r[5],
                              bf, json.dumps({"amount": r[6], "source": "akshare"})))

            conn.commit()
            success += 1
            if i % 50 == 0:
                logger.info(f"  [{i+1}/{len(symbols)}] {symbol}: {len(records) if 'records' in dir() else '?'} rows")
        except Exception as e:
            logger.error(f"  ❌ {symbol}: {e}")
            failed += 1
            conn.rollback()

        if i < len(symbols) - 1:
            time.sleep(3)

    logger.info(f"OHLC complete: {success} success, {failed} failed")
    return success, failed


def fetch_index_ohlc(conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch index OHLC via AKShare. Returns (success, failed)."""
    logger.info(f"=== Fetching Index OHLC (AKShare) for {len(symbols)} indices ===")

    success = 0
    failed = 0

    for symbol in symbols:
        ak_sym = _INDEX_MAP.get(symbol)
        if not ak_sym:
            logger.warning(f"  Unknown index mapping: {symbol}")
            failed += 1
            continue

        try:
            df = ak.stock_zh_index_daily(symbol=ak_sym)
            if df is None or len(df) == 0:
                failed += 1
                continue

            records = []
            for _, row in df.iterrows():
                d = str(row["date"])
                records.append((d, float(row["open"]), float(row["high"]),
                               float(row["low"]), float(row["close"]),
                               int(row["volume"])))
            for r in records:
                cur.execute("""
                    INSERT INTO ohlc (symbol, data_source, timeframe, timestamp,
                                      open, high, low, close, volume, backward_factor, data)
                    VALUES (%s, 'akshare', '1d', %s::date, %s, %s, %s, %s, %s, 1.0, %s)
                    ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                        open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                        close = EXCLUDED.close, volume = EXCLUDED.volume,
                        backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                """, (symbol, r[0], r[1], r[2], r[3], r[4], r[5],
                      json.dumps({"amount": 0, "source": "akshare"})))
            conn.commit()
            success += 1
            logger.info(f"  {symbol}: {len(records)} rows")
        except Exception as e:
            logger.error(f"  ❌ {symbol}: {e}")
            failed += 1
            conn.rollback()

        time.sleep(3)

    logger.info(f"Index OHLC complete: {success} success, {failed} failed")
    return success, failed


def _parse_akshare_value(val) -> float | None:
    """Parse AKShare financial values: '1.47亿' → 147000000, '23.38%' → 23.38"""
    if val is None or val is False or (isinstance(val, float) and math.isnan(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        if s.endswith("亿"):
            return float(s[:-1]) * 1e8
        elif s.endswith("万"):
            return float(s[:-1]) * 1e4
        elif s.endswith("%"):
            return float(s[:-1])
        else:
            return float(s)
    except ValueError:
        return None


# Column mapping: AKShare → our field names
_AKSHARE_FIELD_MAP = {
    "净利润": "net_income",
    "净利润同比增长率": "net_income_yoy",
    "扣非净利润": "deducted_net_income",
    "扣非净利润同比增长率": "deducted_net_income_yoy",
    "营业总收入": "revenue",
    "营业总收入同比增长率": "revenue_yoy",
    "基本每股收益": "basic_eps",
    "每股净资产": "bps",
    "每股资本公积金": "capital_reserve_per_share",
    "每股未分配利润": "undistributed_profit_per_share",
    "每股经营现金流": "operating_cash_flow_per_share",
    "销售净利率": "net_margin",
    "销售毛利率": "gross_margin",
    "净资产收益率": "roe",
    "净资产收益率-摊薄": "roe_diluted",
    "营业周期": "operating_cycle",
    "存货周转率": "inventory_turnover",
    "存货周转天数": "inventory_turnover_days",
    "应收账款周转天数": "receivables_turnover_days",
    "流动比率": "current_ratio",
    "速动比率": "quick_ratio",
    "保守速动比率": "conservative_quick_ratio",
    "产权比率": "equity_ratio",
    "资产负债率": "debt_to_assets",
}


def _akshare_symbol(symbol: str) -> str:
    """600519.SH → 600519"""
    return symbol.split(".")[0]


def fetch_stock_fundamentals(conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Fetch stock fundamentals via AKShare. Returns (success, failed)."""
    logger.info(f"=== Fetching Stock Fundamentals (AKShare) for {len(symbols)} symbols ===")

    success = 0
    failed = 0

    for i, symbol in enumerate(symbols):
        try:
            ak_sym = _akshare_symbol(symbol)
            df = ak.stock_financial_abstract_ths(symbol=ak_sym, indicator="按报告期")

            if df is None or len(df) == 0:
                logger.warning(f"  [{i+1}/{len(symbols)}] {symbol}: no data")
                failed += 1
                continue

            # Parse each report period
            inserted = 0
            for _, row in df.iterrows():
                report_date = str(row["报告期"])  # e.g. "2025-12-31"
                if len(report_date) < 10:
                    continue

                parsed = {}
                for akshare_col, our_field in _AKSHARE_FIELD_MAP.items():
                    if akshare_col in df.columns:
                        val = _parse_akshare_value(row[akshare_col])
                        if val is not None:
                            parsed[our_field] = val

                if parsed:
                    cur.execute("""
                        INSERT INTO fundamentals (symbol, data_source, date, category, data)
                        VALUES (%s, 'akshare', %s::date, 'indicators', %s)
                        ON CONFLICT (symbol, data_source, date, category) DO UPDATE SET data = %s
                    """, (symbol, report_date, json.dumps(parsed), json.dumps(parsed)))
                    inserted += 1

            conn.commit()
            success += 1
            if i % 50 == 0:
                logger.info(f"  [{i+1}/{len(symbols)}] {symbol}: {inserted} reports")
        except Exception as e:
            logger.error(f"  ❌ Fundamentals {symbol}: {e}")
            failed += 1
            conn.rollback()

        if i < len(symbols) - 1:
            time.sleep(0.2)

    logger.info(f"Fundamentals complete: {success} success, {failed} failed")
    return success, failed


def fetch_etf_fundamentals(conn, cur) -> tuple[int, int]:
    """ETF fundamentals: skip for now. Returns (0, 0)."""
    logger.info("=== ETF Fundamentals: skipped (no source) ===")
    return 0, 0


def validate_etf_prices(conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Friday sweep: detect ETF splits/dividends by comparing latest Sina close vs stored.
    
    ETFs store raw prices with bf=1.0. If a split/dividend occurred, the stored
    price for the latest date will differ from Sina's latest close.
    When detected, refetch full history for that ETF.
    Returns (checked, refetched).
    """
    from farseer.data.universe import is_etf
    logger.info(f"=== Friday ETF Sweep for {len(symbols)} ETFs ===")

    checked = 0
    refetched = 0

    for symbol in symbols:
        if not is_etf(symbol):
            continue
        try:
            # Get latest stored row
            cur.execute(
                "SELECT timestamp::date, close FROM ohlc "
                "WHERE symbol=%s AND data_source='akshare' AND timeframe='1d' "
                "ORDER BY timestamp DESC LIMIT 1",
                (symbol,),
            )
            row = cur.fetchone()
            if not row:
                continue
            latest_date, stored_close = row
            stored_close = float(stored_close)
            date_str = str(latest_date)

            # Fetch latest from Sina
            sina_sym = to_sina_symbol(symbol)
            df = ak.fund_etf_hist_sina(symbol=sina_sym)
            if df is None or len(df) == 0:
                continue
            checked += 1

            # Find matching date in Sina data
            sina_close = None
            for _, r in df.iterrows():
                if str(r["date"]) == date_str:
                    sina_close = float(r["close"])
                    break

            if sina_close is None:
                continue

            # Check if price changed (>1% indicates split/dividend adjustment)
            if abs(stored_close - sina_close) / stored_close < 0.01:
                continue

            logger.warning(f"  ⚠️  ETF {symbol}: stored={stored_close:.4f} sina={sina_close:.4f}, rescanning...")

            # Refetch full history
            records = []
            for _, r in df.iterrows():
                d = str(r["date"])
                d_str = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d) == 8 and "-" not in d else d[:10]
                records.append((d_str, float(r["open"]), float(r["high"]),
                               float(r["low"]), float(r["close"]),
                               int(r["volume"]), float(r.get("amount", 0) or 0)))

            for r in records:
                cur.execute("""
                    INSERT INTO ohlc (symbol, data_source, timeframe, timestamp,
                                      open, high, low, close, volume, backward_factor, data)
                    VALUES (%s, 'akshare', '1d', %s::date, %s, %s, %s, %s, %s, 1.0, %s)
                    ON CONFLICT (symbol, data_source, timeframe, timestamp) DO UPDATE SET
                        open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                        close = EXCLUDED.close, volume = EXCLUDED.volume,
                        backward_factor = EXCLUDED.backward_factor, data = EXCLUDED.data
                """, (symbol, r[0], r[1], r[2], r[3], r[4], r[5],
                      json.dumps({"amount": r[6], "source": "akshare"})))

            conn.commit()
            refetched += 1
            logger.info(f"  ✅ ETF {symbol}: {len(records)} rows refetched")

        except Exception as e:
            logger.error(f"  ❌ ETF sweep {symbol}: {e}")
            conn.rollback()

        time.sleep(3)

    logger.info(f"ETF sweep done: {checked} checked, {refetched} refetched")
    return checked, refetched


def validate_backward_factors(conn, cur, symbols: list[str]) -> tuple[int, int]:
    """Weekly sweep: check if any stocks had splits/dividends that changed bf.
    
    For each stock: fetch hfq from Sina, compare latest hfq/raw ratio vs stored bf.
    If changed, recompute all bf values. Runs Fridays only.
    Returns (checked, updated).
    """
    logger.info(f"=== Weekly BF Sweep for {len(symbols)} stocks ===")
    
    checked = 0
    updated = 0
    
    for i, symbol in enumerate(symbols):
        try:
            # Get stored bf from most recent row
            cur.execute(
                "SELECT timestamp::date, close, backward_factor FROM ohlc "
                "WHERE symbol=%s AND data_source='akshare' AND timeframe='1d' "
                "ORDER BY timestamp DESC LIMIT 1",
                (symbol,),
            )
            row = cur.fetchone()
            if not row:
                continue
            latest_date, raw_close, stored_bf = row
            stored_bf = float(stored_bf)
            raw_close = float(raw_close)
            
            if raw_close <= 0:
                continue
            
            # Fetch hfq from Sina
            sina_sym = to_sina_symbol(symbol)
            df = ak.stock_zh_a_daily(symbol=sina_sym, adjust="hfq")
            if df is None or len(df) == 0:
                continue
            
            # Find today's/latest hfq close
            latest_date_str = str(latest_date)
            hfq_close = None
            for _, r in df.iterrows():
                if str(r["date"]) == latest_date_str:
                    hfq_close = float(r["close"])
                    break
            
            if hfq_close is None or hfq_close <= 0:
                continue
            
            current_bf = hfq_close / raw_close
            checked += 1
            
            # Check if bf changed (0.5% tolerance for rounding)
            if abs(current_bf - stored_bf) / stored_bf < 0.005:
                if i % 100 == 0:
                    logger.info(f"  [{i+1}/{len(symbols)}] {symbol}: bf unchanged")
                continue
            
            # BF changed! Recompute all bf values
            logger.warning(f"  ⚠️  {symbol}: bf changed {stored_bf:.4f} → {current_bf:.4f}, rescanning...")
            
            # Build hfq lookup
            hfq_map = {}
            for _, r in df.iterrows():
                hfq_map[str(r["date"])] = float(r["close"])
            
            # Get all DB rows for this stock
            cur.execute(
                "SELECT id, timestamp::date, close FROM ohlc "
                "WHERE symbol=%s AND data_source='akshare' AND timeframe='1d'",
                (symbol,),
            )
            updates = 0
            for db_row in cur.fetchall():
                row_id, date_val, db_close = db_row
                date_str = str(date_val)
                if date_str in hfq_map and float(db_close) > 0:
                    new_bf = hfq_map[date_str] / float(db_close)
                    cur.execute("UPDATE ohlc SET backward_factor=%s WHERE id=%s", (new_bf, row_id))
                    updates += 1
            conn.commit()
            updated += 1
            logger.info(f"  ✅ {symbol}: {updates} rows updated")
            
        except Exception as e:
            logger.error(f"  ❌ BF sweep {symbol}: {e}")
            conn.rollback()
        
        if i < len(symbols) - 1:
            time.sleep(3)
    
    logger.info(f"BF sweep done: {checked} checked, {updated} had changes")
    return checked, updated


def fetch_macro_to_db(conn, cur) -> tuple[int, int]:
    """Fetch macro data and store in DB. Returns (inserted, errors)."""
    logger.info("=== Fetching Macro Economic Data ===")
    try:
        records = fetch_all_macro()
        if not records:
            logger.warning("Macro: no records fetched")
            return 0, 0

        inserted = 0
        errors = 0
        for r in records:
            try:
                cur.execute("""
                    INSERT INTO macro (symbol, data_source, date, value, data)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, data_source, date) DO UPDATE SET
                        value = EXCLUDED.value, data = EXCLUDED.data
                """, (r.symbol, r.data_source.value, r.date, r.value,
                      json.dumps(r.data or {})))
                inserted += 1
            except Exception as e:
                logger.error(f"Macro insert failed {r.symbol}/{r.date}: {e}")
                errors += 1

        conn.commit()
        logger.info(f"Macro complete: {inserted} inserted, {errors} errors")
        return inserted, errors
    except Exception as e:
        logger.exception(f"Macro fetch failed: {e}")
        return 0, 1


def daily_fetch_job():
    """Daily fetch: update all universe symbols with latest data via AKShare."""
    import psycopg2
    from farseer.config import settings

    logger.info("Daily fetch job starting (AKShare)...")

    if is_market_closed():
        logger.info("Skipping fetch - market is closed")
        conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
        cur = conn.cursor()
        _log_task_skip(conn, cur)
        cur.close()
        conn.close()
        return

    conn = psycopg2.connect(settings.database_url_sync.replace("+psycopg2", ""))
    cur = conn.cursor()
    task_id = _log_task_start(conn, cur)

    try:
        symbols = get_all_symbols()
        stock_symbols, etf_symbols = split_by_type(symbols)
        logger.info(f"Daily fetch: {len(stock_symbols)} stocks, {len(etf_symbols)} ETFs")

        ohlc_success, ohlc_failed = fetch_ohlc(conn, cur, symbols)
        idx_success, idx_failed = fetch_index_ohlc(conn, cur, INDICES)
        fund_success, fund_failed = fetch_stock_fundamentals(conn, cur, stock_symbols)
        etf_success, etf_failed = fetch_etf_fundamentals(conn, cur)
        macro_inserted, macro_errors = fetch_macro_to_db(conn, cur)

        # Friday: validate backward_factor + ETF price integrity
        if date.today().weekday() == 4:  # Monday=0, Friday=4
            bf_checked, bf_updated = validate_backward_factors(conn, cur, stock_symbols)
            etf_checked, etf_refetched = validate_etf_prices(conn, cur, etf_symbols)
        else:
            bf_checked, bf_updated = 0, 0
            etf_checked, etf_refetched = 0, 0

        result = {
            "ohlc": {"success": ohlc_success, "failed": ohlc_failed},
            "index": {"success": idx_success, "failed": idx_failed},
            "fundamentals": {"success": fund_success, "failed": fund_failed},
            "etf": {"success": etf_success, "failed": etf_failed},
            "macro": {"inserted": macro_inserted, "errors": macro_errors},
            "bf_sweep": {"checked": bf_checked, "updated": bf_updated},
            "etf_sweep": {"checked": etf_checked, "refetched": etf_refetched},
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
