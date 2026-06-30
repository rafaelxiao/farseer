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

from farseer.sources.datasource import DataSource
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
    """US CPI YoY% — uses _yoy variant for fresher data (through 2026-06)."""
    try:
        df = ak.macro_usa_cpi_yoy()
        if df is None or len(df) == 0:
            return []
        # Columns: 时间, 发布日期, 现值, 前值
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("时间"))
            v = _safe_float(row.get("现值"))
            prev = _safe_float(row.get("前值"))
            if d is not None and v is not None:
                records.append(MacroBase(
                    symbol="CPI.US", data_source=DataSource.akshare, date=d, value=v,
                    data={"previous": prev} if prev is not None else None,
                ))
        logger.info(f"US CPI YoY: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US CPI YoY failed: {e}")
        return []


def fetch_us_cpi_level() -> list[MacroBase]:
    """US CPI absolute level (monthly) — historical back to 1970."""
    try:
        df = ak.macro_usa_cpi_monthly()
        records = _standard_extract(df, "CPI_LEVEL.US")
        logger.info(f"US CPI Level: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US CPI Level failed: {e}")
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


# ── Additional China Indicators ──

def fetch_rrr() -> list[MacroBase]:
    """China Reserve Requirement Ratio."""
    try:
        df = ak.macro_china_reserve_requirement_ratio()
        if df is None or len(df) == 0:
            return []
        # Columns: 公布时间, 生效时间, 大型金融机构-调整后, ...
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("生效时间"))
            v = _safe_float(row.get("大型金融机构-调整后"))
            if d is not None and v is not None:
                records.append(MacroBase(symbol="RRR.CN", data_source=DataSource.akshare, date=d, value=v))
        logger.info(f"RRR: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"RRR failed: {e}")
        return []


def fetch_trade_balance() -> list[MacroBase]:
    """China Trade Balance (亿美元)."""
    try:
        df = ak.macro_china_trade_balance()
        if df is None or len(df) == 0:
            return []
        records = _standard_extract(df, "TRADE_BALANCE.CN")
        logger.info(f"Trade Balance: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"Trade Balance failed: {e}")
        return []


def fetch_industrial_production() -> list[MacroBase]:
    """China Industrial Production YoY%."""
    try:
        df = ak.macro_china_industrial_production_yoy()
        if df is None or len(df) == 0:
            return []
        records = _standard_extract(df, "INDUSTRIAL_PROD.CN")
        logger.info(f"Industrial Production: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"Industrial Production failed: {e}")
        return []


def fetch_social_financing() -> list[MacroBase]:
    """China Social Financing (亿元)."""
    try:
        df = ak.macro_china_new_financial_credit()
        if df is None or len(df) == 0:
            return []
        # Columns: 月份, 当月, 当月-同比增长, ...
        records = []
        for _, row in df.iterrows():
            d = _parse_date(row.get("月份"))
            v = _safe_float(row.get("当月"))
            if d is not None and v is not None:
                records.append(MacroBase(symbol="SOCIAL_FIN.CN", data_source=DataSource.akshare, date=d, value=v))
        logger.info(f"Social Financing: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"Social Financing failed: {e}")
        return []


def fetch_urban_unemployment() -> list[MacroBase]:
    """China Urban Unemployment Rate."""
    try:
        df = ak.macro_china_urban_unemployment()
        if df is None or len(df) == 0:
            return []
        records = _standard_extract(df, "UNEMPLOY.CN")
        logger.info(f"Urban Unemployment: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"Urban Unemployment failed: {e}")
        return []


# ── Additional US Indicators ──

def fetch_us_core_cpi() -> list[MacroBase]:
    """US Core CPI (ex food & energy)."""
    try:
        df = ak.macro_usa_core_cpi_monthly()
        records = _standard_extract(df, "CORE_CPI.US")
        logger.info(f"US Core CPI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US Core CPI failed: {e}")
        return []


def fetch_us_retail() -> list[MacroBase]:
    """US Retail Sales."""
    try:
        df = ak.macro_usa_retail_sales()
        records = _standard_extract(df, "RETAIL.US")
        logger.info(f"US Retail: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US Retail failed: {e}")
        return []


def fetch_us_ism_pmi() -> list[MacroBase]:
    """US ISM Manufacturing PMI."""
    try:
        df = ak.macro_usa_ism_pmi()
        records = _standard_extract(df, "ISM_PMI.US")
        logger.info(f"US ISM PMI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US ISM PMI failed: {e}")
        return []


def fetch_us_ppi() -> list[MacroBase]:
    """US PPI."""
    try:
        df = ak.macro_usa_ppi()
        records = _standard_extract(df, "PPI.US")
        logger.info(f"US PPI: {len(records)} records")
        return records
    except Exception as e:
        logger.error(f"US PPI failed: {e}")
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
    fetch_rrr,
    fetch_trade_balance,
    fetch_industrial_production,
    fetch_social_financing,
    fetch_urban_unemployment,
    # US
    fetch_us_cpi,
    fetch_us_cpi_level,
    fetch_us_core_cpi,
    fetch_us_rate,
    fetch_us_unemployment,
    fetch_us_nonfarm,
    fetch_us_retail,
    fetch_us_ism_pmi,
    fetch_us_ppi,
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
