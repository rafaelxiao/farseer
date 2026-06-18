# Farseer Project Rules

## Package Management
- **Use `uv`** for Python package management (not pip)
- Add dependency: `uv add <package>`
- Sync dependencies: `uv sync`
- Mirror: Tsinghua mirror configured at `~/.config/uv/uv.toml`

## API Keys
- **Tushare token**: stored in `.env.dev` / `.env.prod` as `TUSHARE_TOKEN`

## Symbol Format
- Farseer internal: `{CODE}.{EXCHANGE}` (e.g., `600519.SH`, `159915.SZ`)
- Baostock: `sh.600519`, `sz.159915`
- Tushare: `600519.SH`, `159915.SZ`
- Yahoo Finance: `600519.SS` (Shanghai), `000858.SZ` (Shenzhen)
- Binance: `BTCUSDT`, `ETHUSDT`

## Ports
| Service | Dev | Prod |
|---------|-----|------|
| Backend | 8173 | 8174 |
| Frontend | 5173 | 5174 |
| DB | 5432 | 5433 |

## Data Sources

### Supported Sources (5 total)

| Source | Markets | OHLC | Fundamentals | Status |
|--------|---------|------|--------------|--------|
| **Tushare** | A-shares, ETFs | ✅ Full history | ✅ Income, Balance, Indicators | **Active** |
| **AKShare** | A-shares, ETFs | ✅ | ✅ | Available |
| **Baostock** | A-shares | ✅ Full history | ✅ Basic | Available |
| **Yahoo Finance** | Global stocks, ETFs | ✅ | ✅ Basic | Available |
| **Binance** | Crypto | ✅ Full history | ✅ Market data | Available |

### Currently Active
- **OHLC**: Tushare (full history with adj_factor)
- **Fundamentals**: Tushare (income, balance_sheet, financial_indicator, valuation, dividend)
- **ETF Stats**: Tushare (fund_daily, fund_nav, fund_adj)

### Data Coverage
- **A-share stocks**: CSI 300 + CSI 500 (~1,200 symbols)
- **ETFs**: Top 87 liquid ETFs
- **History**: Full IPO-to-present for most symbols
- **Adjustment**: Store 后复权 with `backward_factor`, API converts to 前复权 on-the-fly

## Daily Fetch
- **Schedule**: 18:00 CST (after market close at 15:00)
- **OHLC**: Fetch last 3 days (catch any missed days)
- **Fundamentals**: Stocks only (income, balance, indicators)
- **ETF Stats**: NAV data
- **Skip**: Weekends and Chinese market holidays
