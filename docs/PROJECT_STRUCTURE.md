# Farseer - Project Structure

```
farseer/
├── docs/
│   ├── DESIGN_DECISIONS.md
│   └── PROJECT_STRUCTURE.md
│
├── backend/
│   ├── src/
│   │   └── farseer/
│   │       ├── __init__.py
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── database.py
│   │       │
│   │       ├── models/
│   │       │   ├── base.py
│   │       │   ├── ohlc.py
│   │       │   ├── fundamentals.py
│   │       │   └── task.py
│   │       │
│   │       ├── schemas/
│   │       │   ├── ohlc.py
│   │       │   ├── fundamentals.py
│   │       │   └── task.py
│   │       │
│   │       ├── api/
│   │       │   ├── deps.py
│   │       │   └── v1/
│   │       │       ├── router.py
│   │       │       ├── ohlc.py
│   │       │       ├── fundamentals.py
│   │       │       └── tasks.py
│   │       │
│   │       ├── services/
│   │       │   ├── ohlc.py
│   │       │   └── fundamentals.py
│   │       │
│   │       ├── symbols/              # Symbol system
│   │       │   ├── formats.py        # Canonical format: {CODE}.{EXCHANGE}
│   │       │   └── converter.py      # Convert between source formats
│   │       │
│   │       ├── fetchers/             # Data source fetchers
│   │       │   ├── base.py           # BaseFetcher abstract class
│   │       │   ├── registry.py       # FetcherRegistry
│   │       │   └── sources/
│   │       │       ├── yfinance_fetcher.py
│   │       │       └── baostock_fetcher.py
│   │       │
│   │       ├── scheduler/
│   │       │   ├── runner.py
│   │       │   └── jobs.py
│   │       │
│   │       └── utils/
│   │
│   ├── tests/
│   ├── migrations/
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
│
├── scripts/
│   └── start.sh
│
├── .env.dev
├── .env.prod
└── README.md
```

---

## Symbol System

**Format:** `{CODE}.{EXCHANGE}`

| Symbol | Exchange | Description |
|--------|----------|-------------|
| `600519.SH` | Shanghai | Moutai |
| `000858.SZ` | Shenzhen | Wuliangye |
| `0700.HK` | Hong Kong | Tencent |
| `AAPL` | US | Apple (no suffix) |

**Source Conversions:**

| Source | Format | Example |
|--------|--------|---------|
| Farseer | `{CODE}.{EXCHANGE}` | `600519.SH` |
| yfinance | `{CODE}.SS/.SZ` | `600519.SS` |
| baostock | `{prefix}.{CODE}` | `sh.600519` |
| tushare | `{CODE}.{EXCHANGE}` | `600519.SH` (same!) |

---

## Fetcher Architecture

```
BaseFetcher (abstract)
    ├── YFinanceFetcher
    ├── BaostockFetcher
    └── TushareFetcher (future)
```

Each fetcher:
1. Implements `_fetch_ohlc()` to get data from source
2. Converts source symbols to Farseer format
3. Returns `OHLCBase` records with `adjustor_factor`
4. Auto-registers with `FetcherRegistry`
