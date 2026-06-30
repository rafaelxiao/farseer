import json
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from farseer.api.deps import get_db
from farseer.schemas.fundamentals import FundamentalsBase, FundamentalsOut, FundamentalsQuery
from farseer.data.fundamentals import FundamentalsService

router = APIRouter()


@router.get("/", response_model=list[FundamentalsOut])
async def get_fundamentals(
    symbol: str | None = None,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    service = FundamentalsService(db)
    return await service.get_fundamentals(symbol, category, start_date, end_date, limit)


@router.get("/summary/{symbol}")
async def get_fundamental_summary(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    periods: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """Get fundamental summary for a symbol, grouped by category with multiple periods."""
    query = """
        SELECT category, date, data
        FROM fundamentals
        WHERE symbol = :symbol
    """
    params = {"symbol": symbol}
    
    if start_date:
        query += " AND date >= :start_date"
        params["start_date"] = date.fromisoformat(start_date)
    if end_date:
        query += " AND date <= :end_date"
        params["end_date"] = date.fromisoformat(end_date)
    
    query += " ORDER BY category, date DESC"
    
    result = await db.execute(text(query), params)
    rows = result.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail=f"No fundamentals found for {symbol}")
    
    # Group by category, keep multiple periods
    categories = {}
    for row in rows:
        cat = row[0]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "date": row[1].isoformat() if row[1] else None,
            "data": json.loads(row[2]) if row[2] else {}
        })
    
    # Limit to N periods per category
    for cat in categories:
        categories[cat] = categories[cat][:periods]
    
    # Get available dates
    all_dates = sorted(set(
        item["date"] 
        for items in categories.values() 
        for item in items
    ), reverse=True)
    
    return {"symbol": symbol, "categories": categories, "available_dates": all_dates}


@router.get("/valuation-history/{symbol}")
async def get_valuation_history(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Calculate historical PE, PB, PS by combining OHLC prices with quarterly fundamentals."""
    from datetime import date as date_type
    
    # Get OHLC data
    ohlc_query = """
        SELECT timestamp::date as date, close, backward_factor
        FROM ohlc
        WHERE symbol = :symbol AND timeframe = '1d'
    """
    ohlc_params = {"symbol": symbol}
    
    if start_date:
        ohlc_query += " AND timestamp >= :start_date"
        ohlc_params["start_date"] = date_type.fromisoformat(start_date)
    if end_date:
        ohlc_query += " AND timestamp <= :end_date"
        ohlc_params["end_date"] = date_type.fromisoformat(end_date)
    
    ohlc_query += " ORDER BY timestamp"
    ohlc_result = await db.execute(text(ohlc_query), ohlc_params)
    ohlc_rows = ohlc_result.fetchall()
    
    if not ohlc_rows:
        raise HTTPException(status_code=404, detail=f"No OHLC data found for {symbol}")
    
    # Get quarterly financial data (EPS, BPS, Revenue per share)
    fin_query = """
        SELECT date, category, data
        FROM fundamentals
        WHERE symbol = :symbol AND category IN ('income', 'financial_indicator')
        ORDER BY date
    """
    fin_result = await db.execute(text(fin_query), {"symbol": symbol})
    fin_rows = fin_result.fetchall()
    
    # Build quarterly data lookup
    quarterly = {}  # date -> {eps, bps, rps, revenue, net_income_yoy}
    for row in fin_rows:
        d = json.loads(row[2])
        q_date = row[0]
        if q_date not in quarterly:
            quarterly[q_date] = {}
        if row[1] == 'income':
            quarterly[q_date]['eps'] = d.get('basic_eps')
            quarterly[q_date]['revenue'] = d.get('revenue')
            quarterly[q_date]['net_income'] = d.get('net_income_attr_p')
        elif row[1] == 'financial_indicator':
            quarterly[q_date]['bps'] = d.get('bps')
            quarterly[q_date]['net_income_yoy'] = d.get('net_income_yoy')
            quarterly[q_date]['revenue_yoy'] = d.get('revenue_yoy')
    
    # Sort quarterly dates
    q_dates = sorted(quarterly.keys())
    
    # For each OHLC date, find the most recent quarterly data
    result = []
    q_idx = 0
    latest_q = {}
    
    for ohlc_row in ohlc_rows:
        price_date = ohlc_row[0]
        price = float(ohlc_row[1])
        backward_factor = float(ohlc_row[2])
        
        # Update quarterly data (find most recent quarter before price date)
        while q_idx < len(q_dates) and q_dates[q_idx] <= price_date:
            latest_q = quarterly[q_dates[q_idx]]
            q_idx += 1
        
        # Calculate actual price (前复权)
        actual_price = price / backward_factor
        
        val_data = {"date": price_date.isoformat(), "price": actual_price}
        
        # PE = Price / EPS (annualized)
        if latest_q.get('eps') and latest_q['eps'] > 0:
            val_data['pe'] = round(actual_price / latest_q['eps'], 2)
        
        # PB = Price / BPS
        if latest_q.get('bps') and latest_q['bps'] > 0:
            val_data['pb'] = round(actual_price / latest_q['bps'], 2)
        
        # PS = Price / Revenue Per Share (annualized)
        # Revenue Per Share = Revenue / Shares (Shares = Market Cap / Price)
        # Simplified: PS = Market Cap / Revenue = Price * Shares / Revenue
        # But we can use: PS = Price / (Revenue / Shares) = Price * Shares / Revenue
        # Since we don't have shares, we approximate using EPS and price:
        # If EPS = Net Income / Shares, then Shares = Net Income / EPS
        # So RPS = Revenue / (Net Income / EPS) = Revenue * EPS / Net Income
        # And PS = Price / RPS = Price * Net Income / (Revenue * EPS)
        # But simpler: PS = (Price / EPS) * (Net Income / Revenue) = PE * Net Margin
        # Or just use: PS = PE * (Net Income / Revenue)
        if latest_q.get('eps') and latest_q['eps'] > 0 and latest_q.get('revenue') and latest_q.get('net_income'):
            pe = actual_price / latest_q['eps']
            net_margin = latest_q['net_income'] / latest_q['revenue']
            if net_margin > 0:
                val_data['ps'] = round(pe * net_margin, 2)
        
        # PEG = PE / Earnings Growth Rate (%)
        if val_data.get('pe') and latest_q.get('net_income_yoy') and latest_q['net_income_yoy'] > 0:
            val_data['peg'] = round(val_data['pe'] / latest_q['net_income_yoy'], 2)
        
        result.append(val_data)
    
    return {"symbol": symbol, "data": result}


@router.get("/etf-nav-history/{symbol}")
async def get_etf_nav_history(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get ETF historical NAV and calculate premium/discount."""
    import tushare as ts
    from farseer.sources.tushare.client import get_tushare_pro
    
    pro = get_tushare_pro()
    
    ts_code = symbol
    start = start_date.replace('-', '') if start_date else '20200101'
    end = end_date.replace('-', '') if end_date else datetime.now().strftime('%Y%m%d')
    
    # Get NAV history
    df_nav = pro.fund_nav(ts_code=ts_code, start_date=start, end_date=end)
    if df_nav is None or len(df_nav) == 0:
        raise HTTPException(status_code=404, detail=f"No NAV data found for {symbol}")
    
    # Get daily price
    df_price = pro.fund_daily(ts_code=ts_code, start_date=start, end_date=end)
    
    # Build NAV lookup
    nav_map = {}
    for _, row in df_nav.iterrows():
        nav_date = row.get('nav_date', '')
        if nav_date:
            nav_map[nav_date] = {
                'unit_nav': float(row['unit_nav']) if row.get('unit_nav') else None,
                'accum_nav': float(row['accum_nav']) if row.get('accum_nav') else None,
            }
    
    # Build price lookup
    price_map = {}
    if df_price is not None and len(df_price) > 0:
        for _, row in df_price.iterrows():
            trade_date = row.get('trade_date', '')
            if trade_date:
                price_map[trade_date] = float(row['close']) if row.get('close') else None
    
    # Combine and calculate premium/discount
    result = []
    all_dates = sorted(set(list(nav_map.keys()) + list(price_map.keys())))
    
    for d in all_dates:
        nav = nav_map.get(d)
        price = price_map.get(d)
        
        entry = {'date': f"{d[:4]}-{d[4:6]}-{d[6:8]}"}
        
        if nav and nav.get('unit_nav'):
            entry['nav'] = nav['unit_nav']
        
        if price:
            entry['price'] = price
        
        # Calculate premium/discount
        if price and nav and nav.get('unit_nav') and nav['unit_nav'] > 0:
            entry['premium'] = round((price - nav['unit_nav']) / nav['unit_nav'] * 100, 2)
        
        result.append(entry)
    
    return {"symbol": symbol, "data": result}


@router.post("/", response_model=FundamentalsOut)
async def upsert_fundamentals(
    data: FundamentalsBase,
    db: AsyncSession = Depends(get_db),
):
    """Insert or update fundamentals (upsert)."""
    service = FundamentalsService(db)
    return await service.upsert_fundamentals(data)
