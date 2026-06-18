# OHLC Timeframes Documentation

## Available Timeframes by Source

| Timeframe | Tushare | AKShare | Baostock | Yahoo | Binance |
|-----------|---------|---------|----------|-------|---------|
| **1m** | ❌ Paid | ❌ | ❌ | ✅ 7d | ✅ Full |
| **3m** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **5m** | ❌ Paid | ✅ Recent | ✅ Recent | ✅ 60d | ✅ Full |
| **15m** | ❌ Paid | ✅ Recent | ✅ Recent | ✅ 60d | ✅ Full |
| **30m** | ❌ Paid | ✅ Recent | ✅ Recent | ✅ 60d | ✅ Full |
| **1h** | ❌ Paid | ✅ Recent | ✅ Recent | ✅ 730d | ✅ Full |
| **2h** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **4h** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **6h** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **8h** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **12h** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **1d** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **3d** | ❌ | ❌ | ❌ | ❌ | ✅ Full |
| **1w** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |
| **1M** | ✅ Full | ✅ Full | ✅ Full | ✅ Full | ✅ Full |

## Coverage Summary

### A-shares (Tushare, AKShare, Baostock)
- **Full history (free)**: 1d, 1w, 1M
- **Tushare paid**: 1m (~1-2yr), 5m/15m/30m/1h (~2-5yr)
- **AKShare/Baostock free**: 5m/15m/30m/1h (recent data only, ~few months)

### Global Stocks (Yahoo Finance)
- **Full history**: 1d, 1w, 1M
- **Last 730 days**: 1h
- **Last 60 days**: 5m, 15m, 30m, 90m
- **Last 7 days**: 1m, 2m

### Crypto (Binance)
- **Full history**: All timeframes (1m to 1M)

## Tushare Permission Levels

| Level | Daily/Weekly/Monthly | Intraday | Price |
|-------|---------------------|----------|-------|
| Free | ✅ | ❌ | Free |
| Basic | ✅ | ✅ | ¥200/year |
| Pro | ✅ | ✅ (more history) | ¥500+/year |

**Note**: Intraday history depth depends on subscription level.

## Farseer Timeframe Codes

| Code | Duration | Common Use |
|------|----------|------------|
| `1m` | 1 minute | Scalping, HFT |
| `3m` | 3 minutes | Short-term trading |
| `5m` | 5 minutes | Day trading |
| `15m` | 15 minutes | Day trading |
| `30m` | 30 minutes | Swing trading |
| `1h` | 1 hour | Swing trading |
| `2h` | 2 hours | Position trading |
| `4h` | 4 hours | Position trading |
| `6h` | 6 hours | Position trading |
| `8h` | 8 hours | Position trading |
| `12h` | 12 hours | Position trading |
| `1d` | 1 day | Long-term investing |
| `3d` | 3 days | Long-term investing |
| `1w` | 1 week | Long-term investing |
| `1M` | 1 month | Portfolio analysis |

## Usage Examples

### Fetch Daily Data (Full History - Free)
```python
fetcher = FetcherRegistry.get("tushare")
records = await fetcher.fetch_ohlc("600519.SH", "1d", "1990-01-01", "2026-01-01")
```

### Fetch Hourly Data (Yahoo Finance - Free)
```python
fetcher = FetcherRegistry.get("yfinance")
records = await fetcher.fetch_ohlc("AAPL.US", "1h", "2024-01-01", "2026-01-01")
```

### Fetch 5-Minute Data (Binance - Free, Full History)
```python
fetcher = FetcherRegistry.get("binance")
records = await fetcher.fetch_ohlc("BTC.USDT", "5m", "2020-01-01", "2026-01-01")
```

## Storage Considerations

| Timeframe | Records/Year | Storage/Year |
|-----------|--------------|--------------|
| 1m | ~525,600 | ~50 MB |
| 5m | ~105,120 | ~10 MB |
| 15m | ~35,040 | ~3.5 MB |
| 30m | ~17,520 | ~1.7 MB |
| 1h | ~8,760 | ~0.9 MB |
| 1d | ~365 | ~0.04 MB |
| 1w | ~52 | ~0.005 MB |
| 1M | ~12 | ~0.001 MB |

## Recommendations

1. **Daily/Weekly/Monthly A-shares**: Use Tushare (free, full history)
2. **Intraday A-shares**: 
   - Free: AKShare/Baostock (recent data only)
   - Paid: Tushare (2-5 year history)
3. **Global Stocks**: Use Yahoo Finance (free, 730d for 1h)
4. **Crypto**: Use Binance (free, full history for all timeframes)
