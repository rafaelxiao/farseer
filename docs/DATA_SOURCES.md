# Data Sources Documentation

## Overview

Farseer supports 5 data sources for market data. Each source has different capabilities and coverage.

| Source | Markets | OHLC | Fundamentals | Adjustment | Status |
|--------|---------|------|--------------|------------|--------|
| **Tushare** | A-shares, ETFs | ✅ Full history | ✅ Income, Balance, Indicators | adj_factor | **Active** |
| **AKShare** | A-shares, ETFs | ✅ | ✅ | raw/hfq ratio | Available |
| **Baostock** | A-shares | ✅ Full history | ✅ Basic | 后复权/前复权 ratio | Available |
| **Yahoo Finance** | Global stocks, ETFs | ✅ | ✅ Basic | Adj Close/Close | Available |
| **Binance** | Crypto | ✅ Full history | ✅ Market data | N/A (1.0) | Available |

## Adjustment Factor Calculation

All fetchers calculate `backward_factor` (后复权因子) using the same principle:
- **IPO date**: backward_factor = 1.0
- **After splits/dividends**: backward_factor increases
- **Formula**: backward_factor = current_ratio / first_ratio

### Tushare
```python
# Uses adj_factor from tushare API
# Normalizes so first date = 1.0
backward_factor = adj_factor / first_adj_factor
```

### AKShare
```python
# Fetches both raw (不复权) and 后复权 prices
# Calculates ratio and normalizes
backward_factor = (hfq_close / raw_close) / first_ratio
```

### Baostock
```python
# Fetches both 后复权 and 前复权 prices
# Calculates ratio and normalizes
backward_factor = (hfq_close / qfq_close) / first_ratio
```

### Yahoo Finance
```python
# Uses Adj Close / Close ratio
# Normalizes so first date = 1.0
backward_factor = (adj_close / close) / first_ratio
```

### Binance
```python
# Crypto has no splits/dividends
backward_factor = 1.0  # Always
```

## Symbol Format Conversion

| Source | Input Format | Example |
|--------|--------------|---------|
| Farseer | `{CODE}.{EXCHANGE}` | `600519.SH` |
| Tushare | `{CODE}.{EXCHANGE}` | `600519.SH` |
| AKShare | `{CODE}` | `600519` |
| Baostock | `{exchange}.{code}` | `sh.600519` |
| Yahoo Finance | `{CODE}.{SUFFIX}` | `600519.SS` |
| Binance | `{BASE}{QUOTE}` | `BTCUSDT` |

## Exchange Mapping

| Farseer | Tushare | AKShare | Baostock | Yahoo | Binance |
|---------|---------|---------|----------|-------|---------|
| SH | SH | SH | sh | .SS | - |
| SZ | SZ | SZ | sz | .SZ | - |
| US | - | - | - | (none) | - |
| HK | - | - | - | .HK | - |
| CRYPTO | - | - | - | - | (pairs) |

## Usage Example

```python
from farseer.fetchers.registry import FetcherRegistry

# Get fetcher
fetcher = FetcherRegistry.get("tushare")

# Fetch OHLC
records = await fetcher.fetch_ohlc(
    symbol="600519.SH",
    timeframe="1d",
    start="2020-01-01",
    end="2020-12-31"
)

# Each record has:
# - symbol, timeframe, timestamp
# - open, high, low, close, volume
# - backward_factor (后复权因子)
# - data (extra info like amount, source)
```

## API Endpoints

### Fetch OHLC
```http
GET /api/v1/ohlc/?symbol=600519.SH&timeframe=1d&adjust=backward
```

### Fetch Fundamentals
```http
GET /api/v1/fundamentals/summary/600519.SH
```

### Trigger Fetch Job
```http
POST /api/v1/fetch/start?symbols=600519.SH,000858.SZ
```

## Rate Limits

| Source | Limit | Delay |
|--------|-------|-------|
| Tushare | 200 req/min | 0.6s/request |
| AKShare | ~100 req/min | 0.6s/request |
| Baostock | No limit | - |
| Yahoo Finance | ~100 req/min | 0.6s/request |
| Binance | 1200 req/min | 0.1s/request |

## Dependencies

```toml
# Required for all sources
tushare = ">=1.0"
akshare = ">=1.0"
baostock = ">=0.8"
yfinance = ">=0.2"
requests = ">=2.0"
```

## Error Handling

All fetchers handle errors gracefully:
- Network errors: Retry with backoff
- Rate limits: Automatic delay
- Invalid symbols: Skip with warning
- No data: Return empty list

## Testing

```bash
# Test all fetchers
cd backend && source .venv/bin/activate
PYTHONPATH=src python3 -c "
from farseer.fetchers.registry import FetcherRegistry
from farseer.fetchers.sources import *

for name in FetcherRegistry.list_all():
    fetcher = FetcherRegistry.get(name)
    print(f'{name}: {fetcher.supported_exchanges}')
"
```
