"""AKShare macro-economic data fetcher.

Fetches Chinese and US macro indicators and returns MacroBase records.
Extensible: add new fetch_xxx() function and register it in FETCHERS.

AKShare function naming:
  - Chinese: macro_china_xxx (returns DataFrame with 商品/日期/今值/前值)
  - US: macro_usa_xxx (same structure)
"""

import logging
import re
from datetime import date, datetime
from typing import Optional

import akshare as ak
import pandas as pd

from farseer.datasource import DataSource
from farseer.schemas.macro import MacroBase

logger = logging.getLogger(__name__)


# ── Date Parsing ──

def _parse_date(val) -> Optional[date]:
    """Parse various AKShare date formats."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    s = str(val).strip()
    if not s:
        return None
    # "2026年05月份" → 2026-05-01
    m = re.match(r"(\d{4})年(\d{1,2})月", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), 1)
    # Standard formats
    for fmt in ["%Y-%m-%d", "%Y-%m", "%Y%m%d", "%Y%m"]:
        try:
            return datetime.strptime(s[:len(fmt)], fmt).date()
        except (ValueError, IndexError):
            continue
    # "2021Q1"
    m = re.match(r"(\d{4})Q(\d)", s)
    if m:
        q = int(m.group(2))
        return date(int(m.group(1)), (q - 1) * 3 + 1, 1)
    return None


def _safe_float(val) -> Optional[float]:
    """Convert to float, return None if not possible."""
    if val is None:
        return None
    try:
        f = float(val)
        if pd.isna(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


def _standard_extract(df: pd.DataFrame, symbol: str) -> list[MacroBase]:
    """Extract records from standard AKShare macro format (商品, 日期, 今值, 前值)."""
    if df is None or len(df) == 0:
        return []
    records = []
    for _, row in df.iterrows():
        d = _parse_date(row.get("日期"))
        v = _safe_float(row.get("今值"))
        prev = _safe_float(row.get("前值"))
        if d is not None and v is not None:
            records.append(MacroBase(
                symbol=symbol, data_source=DataSource.akshare, date=d, value=v,
                data={"previous": prev} if prev is not None else None,
            ))
    return records


# ── Chinese Macro Indicators ──

def fetch_cpi() -> list[MacroBase]:
    """China CPI monthly. value=YoY%, data.previous=前值"""
    try:
        df = ak.macro_china_cpi_monthly()
        records = _standard_extract(df, "CPI.CN")
        logger.info(f"CPI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"CPI failed: {e}")
        return []


def fetch_ppi() -> list[MacroBase]:
    """China PPI monthly. value=YoY%"""
    try:
        df = ak.macro_china_ppi_yearly()
        records = _standard_extract(df, "PPI.CN")
        logger.info(f"PPI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"PPI failed: {e}")
        return []


def fetch_pmi() -> list[MacroBase]:
    """China Manufacturing PMI."""
    try:
        df = ak.macro_china_pmi_yearly()
        records = _standard_extract(df, "PMI.CN")
        logger.info(f"PMI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"PMI failed: {e}")
        return []


def fetch_gdp() -> list[MacroBase]:
    """China GDP quarterly. value=YoY%"""
    try:
        df = ak.macro_china_gdp_yearly()
        records = _standard_extract(df, "GDP.CN")
        logger.info(f"GDP: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"GDP failed: {e}")
        return []


def fetch_m2() -> list[MacroBase]:
    """China M2 Money Supply. value=YoY%, data.amount=金额(亿元)"""
    try:
        df = ak.macro_china_money_supply()
        if df is None or len(df) == 0:
            return []
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("月份"))
            yoy = _safe_float(row.get("货币和准货币(M2)-同比增长"))
            amount = _safe_float(row.get("货币和准货币(M2)-数量(亿元)"))
            if d is not None and yoy is not None:
                records.append(MacroBase(
                    symbol="M2.CN", data_source=DataSource.akshare, date=d, value=yoy,
                    data={"amount": amount} if amount is not None else None,
                ))
        logger.info(f"M2: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"M2 failed: {e}")
        return []


def fetch_lpr() -> list[MacroBase]:
    """China LPR rates (1Y and 5Y)."""
    try:
        df = ak.macro_china_lpr()
        if df is None or len(df) == 0:
            return []
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("TRADE_DATE") or row.get("日期"))
            lpr1y = _safe_float(row.get("LPR1Y"))
            lpr5y = _safe_float(row.get("LPR5Y"))
            if d is not None:
                if lpr1y is not None:
                    records.append(MacroBase(
                        symbol="LPR1Y.CN", data_source=DataSource.akshare, date=d, value=lpr1y,
                    ))
                if lpr5y is not None:
                    records.append(MacroBase(
                        symbol="LPR5Y.CN", data_source=DataSource.akshare, date=d, value=lpr5y,
                    ))
        logger.info(f"LPR: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"LPR failed: {e}")
        return []


def fetch_fx() -> list[MacroBase]:
    """Fetch USD/CNY exchange rate via currency_boc_safe daily data."""
    try:
        df = ak.currency_boc_safe()
        if df is None or len(df) == 0:
            logger.warning("FX USDCNY: no data")
            return []
        # Columns: 日期, 美元, 欧元, 日元, 港元, ...
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("日期"))
            v = _safe_float(row.get("美元"))  # USD/CNY rate
            if d is not None and v is not None:
                records.append(MacroBase(
                    symbol="FX_USDCNY", data_source=DataSource.akshare, date=d, value=v,
                ))
        logger.info(f"FX: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"FX failed: {e}")
        return []


def fetch_foreign_reserves() -> list[MacroBase]:
    """China foreign exchange reserves (亿美元)."""
    try:
        df = ak.macro_china_fx_gold()
        if df is None or len(df) == 0:
            return []
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("月份"))
            v = _safe_float(row.get("国家外汇储备-数值"))
            if d is not None and v is not None:
                records.append(MacroBase(
                    symbol="FX_RESERVES.CN", data_source=DataSource.akshare, date=d, value=v,
                ))
        logger.info(f"FX Reserves: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"FX Reserves failed: {e}")
        return []


# ── US Macro Indicators ──

def fetch_us_cpi() -> list[MacroBase]:
    """US CPI monthly. value=YoY%"""
    try:
        df = ak.macro_usa_cpi_monthly()
        records = _standard_extract(df, "CPI.US")
        logger.info(f"US CPI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US CPI failed: {e}")
        return []


def fetch_us_rate() -> list[MacroBase]:
    """US Fed Funds Rate."""
    try:
        # Correct function name: macro_bank_usa_interest_rate
        df = ak.macro_bank_usa_interest_rate()
        if df is None or len(df) == 0:
            return []
        # Columns: 日期, 今值, 预测值, 前值 (standard format)
        records = _standard_extract(df, "FEDFUNDS.US")
        logger.info(f"US Rate: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US Rate failed: {e}")
        return []


def fetch_us_unemployment() -> list[MacroBase]:
    """US Unemployment Rate."""
    try:
        df = ak.macro_usa_unemployment_rate()
        records = _standard_extract(df, "UNEMPLOYMENT.US")
        logger.info(f"US Unemployment: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US Unemployment failed: {e}")
        return []


def fetch_us_nonfarm() -> list[MacroBase]:
    """US Non-Farm Payrolls (万人)."""
    try:
        df = ak.macro_usa_non_farm()
        records = _standard_extract(df, "NONFARM.US")
        logger.info(f"US Nonfarm: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US Nonfarm failed: {e}")
        return []


# ── Entry Point ──
# To add new indicators:
# 1. Add a fetch_xxx() function above
# 2. Register it in FETCHERS below
# 3. The daily scheduler and fetch_all_macro() pick it up automatically

FETCHERS = [
    # China
    fetch_cpi,
    fetch_ppi,
    fetch_pmi,
    fetch_gdp,
    fetch_m2,
    fetch_lpr,
    fetch_fx,
    fetch_foreign_reserves,
    # US
    fetch_us_cpi,
    fetch_us_rate,
    fetch_us_unemployment,
    fetch_us_nonfarm,
]


def fetch_all_macro() -> list[MacroBase]:
    """Fetch all registered macro indicators. Returns list ready for upsert."""
    logger.info("Starting macro data fetch...")
    all_records = []
    for fetcher in FETCHERS:
        try:
            all_records.extend(fetcher())
        except Exception as e:
            logger.error(f"Fetcher {fetcher.__name__} failed: {e}")
    logger.info(f"Macro fetch complete: {len(all_records)} total records")
    return all_records
