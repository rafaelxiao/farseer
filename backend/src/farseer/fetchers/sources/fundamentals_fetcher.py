"""
Fundamental data fetcher using tushare.

Fetches different data for stocks vs ETFs:

Stocks:
  - income: revenue, net_profit, EPS
  - balancesheet: total_assets, total_liab, equity
  - fina_indicator: ROE, ROA, gross_margin
  - dividend: dividend history

ETFs:
  - fund_daily: NAV, premium/discount
  - fund_adj: adjust factors (always 1.0 for ETFs)
"""

import asyncio
import json
import logging
import math
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date

from farseer.database import async_session_factory
from farseer.models.fundamentals import Fundamentals
from farseer.config import settings
from farseer.symbols.utils import is_etf

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


def _fetch_stock_fundamentals(symbol: str) -> list[dict]:
    """Fetch stock fundamental data from tushare."""
    import tushare as ts
    from farseer.utils.tushare import get_tushare_pro

    pro = get_tushare_pro()

    ts_code = symbol  # Same format: 600519.SH
    results = []

    try:
        # 1. Income statement (last 12 quarters)
        time.sleep(0.5)
        df_income = pro.income(ts_code=ts_code, fields="ts_code,ann_date,end_date,revenue,operate_profit,total_profit,n_income,n_income_attr_p,basic_eps,diluted_eps")
        if df_income is not None and len(df_income) > 0:
            for _, row in df_income.head(12).iterrows():
                period = row.get('end_date', '')
                if period:
                    try:
                        dt = datetime.strptime(period, "%Y%m%d").date()
                    except:
                        continue

                    data = {
                        "revenue": float(row['revenue']) if row.get('revenue') else None,
                        "operate_profit": float(row['operate_profit']) if row.get('operate_profit') else None,
                        "total_profit": float(row['total_profit']) if row.get('total_profit') else None,
                        "net_income": float(row['n_income']) if row.get('n_income') else None,
                        "net_income_attr_p": float(row['n_income_attr_p']) if row.get('n_income_attr_p') else None,
                        "basic_eps": float(row['basic_eps']) if row.get('basic_eps') else None,
                        "diluted_eps": float(row['diluted_eps']) if row.get('diluted_eps') else None,
                    }
                    # Remove None values
                    data = {k: v for k, v in data.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}

                    if data:
                        results.append({
                            "symbol": symbol,
                            "date": dt,
                            "category": "income",
                            "data": data,
                        })

        # 2. Balance sheet (last 8 quarters)
        time.sleep(0.5)
        df_balance = pro.balancesheet(ts_code=ts_code, fields="ts_code,ann_date,end_date,total_assets,total_cur_assets,total_nca,total_liab,total_cur_liab,total_ncl,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int")
        if df_balance is not None and len(df_balance) > 0:
            for _, row in df_balance.head(8).iterrows():
                period = row.get('end_date', '')
                if period:
                    try:
                        dt = datetime.strptime(period, "%Y%m%d").date()
                    except:
                        continue

                    data = {
                        "total_assets": float(row['total_assets']) if row.get('total_assets') else None,
                        "total_cur_assets": float(row['total_cur_assets']) if row.get('total_cur_assets') else None,
                        "total_liab": float(row['total_liab']) if row.get('total_liab') else None,
                        "total_cur_liab": float(row['total_cur_liab']) if row.get('total_cur_liab') else None,
                        "equity": float(row['total_hldr_eqy_exc_min_int']) if row.get('total_hldr_eqy_exc_min_int') else None,
                    }
                    data = {k: v for k, v in data.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}

                    if data:
                        results.append({
                            "symbol": symbol,
                            "date": dt,
                            "category": "balance_sheet",
                            "data": data,
                        })

        # 3. Financial indicators (last 8 quarters)
        time.sleep(0.5)
        df_fina = pro.fina_indicator(ts_code=ts_code, fields="ts_code,ann_date,end_date,eps,dt_eps,grossprofit_margin,netprofit_margin,roe,roe_waa,roe_dt,roa,npta,roic,roe_yearly,roa_yearly,debt_to_assets,op_yoy,netprofit_yoy,bps,equity_yoy")
        if df_fina is not None and len(df_fina) > 0:
            for _, row in df_fina.head(8).iterrows():
                period = row.get('end_date', '')
                if period:
                    try:
                        dt = datetime.strptime(period, "%Y%m%d").date()
                    except:
                        continue

                    data = {
                        "eps": float(row['eps']) if row.get('eps') else None,
                        "roe": float(row['roe']) if row.get('roe') else None,
                        "roe_dt": float(row['roe_dt']) if row.get('roe_dt') else None,
                        "roa": float(row['roa'] or row.get('roa_yearly')) if row.get('roa') or row.get('roa_yearly') else None,
                        "gross_margin": float(row['grossprofit_margin']) if row.get('grossprofit_margin') else None,
                        "net_margin": float(row['netprofit_margin']) if row.get('netprofit_margin') else None,
                        "debt_to_assets": float(row['debt_to_assets']) if row.get('debt_to_assets') else None,
                        "revenue_yoy": float(row['op_yoy']) if row.get('op_yoy') else None,
                        "net_income_yoy": float(row['netprofit_yoy']) if row.get('netprofit_yoy') else None,
                        "bps": float(row['bps']) if row.get('bps') else None,
                        "roe_yoy": float(row['roe_yoy']) if row.get('roe_yoy') else None,
                    }
                    data = {k: v for k, v in data.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}

                    if data:
                        results.append({
                            "symbol": symbol,
                            "date": dt,
                            "category": "financial_indicator",
                            "data": data,
                        })

        # 4. Valuation metrics (PE, PB, PS)
        time.sleep(0.5)
        df_val = pro.daily_basic(ts_code=ts_code, fields="ts_code,trade_date,pe,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_mv")
        if df_val is not None and len(df_val) > 0:
            latest = df_val.iloc[0]
            val_data = {
                "pe": float(latest['pe']) if latest.get('pe') else None,
                "pb": float(latest['pb']) if latest.get('pb') else None,
                "ps": float(latest['ps']) if latest.get('ps') else None,
                "ps_ttm": float(latest['ps_ttm']) if latest.get('ps_ttm') else None,
                "dividend_yield": float(latest['dv_ttm']) if latest.get('dv_ttm') else None,
                "market_cap": float(latest['total_mv']) if latest.get('total_mv') else None,
            }
            val_data = {k: v for k, v in val_data.items() if v is not None and not (isinstance(v, float) and math.isnan(v))}
            
            if val_data:
                trade_date = latest.get('trade_date', '')
                if trade_date:
                    try:
                        dt = datetime.strptime(trade_date, "%Y%m%d").date()
                        results.append({
                            "symbol": symbol,
                            "date": dt,
                            "category": "valuation",
                            "data": val_data,
                        })
                    except:
                        pass

        # 5. Dividend
        time.sleep(0.5)
        df_div = pro.dividend(ts_code=ts_code, fields="ts_code,ann_date,end_date,div_proc,cash_div_tax,stk_div,stk_bo_rate,stk_co_rate,record_date,ex_date,pay_date,base_date,base_share")
        if df_div is not None and len(df_div) > 0:
            dividends = []
            for _, row in df_div.head(10).iterrows():
                dividends.append({
                    "公告日期": str(row.get('ann_date', '')),
                    "报告期": str(row.get('end_date', '')),
                    "现金分红": float(row['cash_div_tax']) if row.get('cash_div_tax') and str(row['cash_div_tax']) != 'nan' else 0,
                    "送股": float(row['stk_div']) if row.get('stk_div') and str(row['stk_div']) != 'nan' else 0,
                    "转增": float(row['stk_co_rate']) if row.get('stk_co_rate') and str(row['stk_co_rate']) != 'nan' else 0,
                    "除权日": str(row.get('ex_date', '')),
                })

            if dividends:
                results.append({
                    "symbol": symbol,
                    "date": date.today(),
                    "category": "dividend",
                    "data": {"dividends": dividends},
                })

    except Exception as e:
        logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")

    return results


def _fetch_etf_fundamentals(symbol: str) -> list[dict]:
    """Fetch ETF fundamental data from tushare."""
    import tushare as ts
    from farseer.utils.tushare import get_tushare_pro

    pro = get_tushare_pro()

    ts_code = symbol
    results = []

    try:
        # Get ETF basic info
        time.sleep(0.5)
        df_fund = pro.fund_basic(ts_code=ts_code, fields="ts_code,name,management,custodian,fund_type,found_date,list_date,issue_amount,m_fee,c_fee,benchmark")
        if df_fund is not None and len(df_fund) > 0:
            row = df_fund.iloc[0]
            fund_data = {
                "name": str(row.get('name', '')),
                "management": str(row.get('management', '')),
                "fund_type": str(row.get('fund_type', '')),
                "found_date": str(row.get('found_date', '')),
                "list_date": str(row.get('list_date', '')),
                "issue_amount": float(row['issue_amount']) if row.get('issue_amount') else None,
                "m_fee": float(row['m_fee']) if row.get('m_fee') else None,
                "c_fee": float(row['c_fee']) if row.get('c_fee') else None,
                "benchmark": str(row.get('benchmark', '')),
            }
            fund_data = {k: v for k, v in fund_data.items() if v is not None and v != ''}

            results.append({
                "symbol": symbol,
                "date": date.today(),
                "category": "etf_basic",
                "data": fund_data,
            })

        # Get recent NAV and performance
        time.sleep(0.5)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now().replace(day=1)).strftime("%Y%m%d")
        df_nav = pro.fund_nav(ts_code=ts_code, start_date=start_date, end_date=end_date, fields="ts_code,ann_date,end_date,unit_nav,accum_nav,accum_div,net_asset,total_nav,adj_nav")
        if df_nav is not None and len(df_nav) > 0:
            latest = df_nav.iloc[0]
            nav_data = {
                "unit_nav": float(latest['unit_nav']) if latest.get('unit_nav') else None,
                "accum_nav": float(latest['accum_nav']) if latest.get('accum_nav') else None,
                "net_asset": float(latest['net_asset']) if latest.get('net_asset') else None,
                "total_nav": float(latest['total_nav']) if latest.get('total_nav') else None,
            }
            nav_data = {k: v for k, v in nav_data.items() if v is not None}

            results.append({
                "symbol": symbol,
                "date": date.today(),
                "category": "etf_nav",
                "data": nav_data,
            })

    except Exception as e:
        logger.error(f"Failed to fetch ETF fundamentals for {symbol}: {e}")

    return results


def _fetch_fundamentals_sync(symbol: str) -> list[dict]:
    """Sync fetch fundamentals (runs in thread)."""
    if is_etf(symbol):
        return _fetch_etf_fundamentals(symbol)
    else:
        return _fetch_stock_fundamentals(symbol)


async def fetch_fundamentals(symbol: str) -> int:
    """Fetch and store fundamentals for a symbol. Returns count of records added."""
    loop = asyncio.get_event_loop()
    records = await loop.run_in_executor(_executor, _fetch_fundamentals_sync, symbol)

    if not records:
        return 0

    async with async_session_factory() as db:
        count = 0
        for rec in records:
            try:
                from sqlalchemy import select, and_
                existing = await db.execute(
                    select(Fundamentals).where(
                        and_(
                            Fundamentals.symbol == rec["symbol"],
                            Fundamentals.date == rec["date"],
                            Fundamentals.category == rec["category"],
                        )
                    )
                )
                existing_rec = existing.scalar_one_or_none()

                if existing_rec:
                    existing_rec.data = json.dumps(rec["data"], ensure_ascii=False)
                else:
                    new_rec = Fundamentals(
                        symbol=rec["symbol"],
                        date=rec["date"],
                        category=rec["category"],
                        data=json.dumps(rec["data"], ensure_ascii=False),
                    )
                    db.add(new_rec)

                count += 1
            except Exception as e:
                logger.error(f"Failed to save fundamental for {symbol}: {e}")

        await db.commit()
        return count


async def fetch_all_fundamentals(symbols: list[str]) -> dict:
    """Fetch fundamentals for all symbols."""
    success = 0
    failed = 0

    for i, symbol in enumerate(symbols):
        try:
            count = await fetch_fundamentals(symbol)
            if count > 0:
                success += 1
            else:
                failed += 1

            if (i + 1) % 50 == 0:
                logger.info(f"Fundamentals: [{i+1}/{len(symbols)}] {success} success, {failed} failed")

        except Exception as e:
            failed += 1
            logger.error(f"Failed {symbol}: {e}")

    return {"success": success, "failed": failed}
