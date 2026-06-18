# Farseer

Market data server for OHLC, fundamentals, and more.

## Ports

| Service | Dev | Prod |
|---------|-----|------|
| Backend | 8173 | 8174 |
| Frontend | 5173 | 5174 |
| Postgres | 5432 | 5433 |

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Bun](https://bun.sh)
- Docker (for database)

### Development

```bash
# 1. Start database
cd docker && docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db

# 2. Setup backend
cd backend
cp ../.env.dev .env
uv sync
uv run alembic upgrade head
uv run uvicorn farseer.main:app --reload --host 0.0.0.0 --port 8173

# 3. Setup frontend (new terminal)
cd frontend
bun install
bun dev
```

Access:
- Frontend: http://localhost:5173
- API: http://localhost:8173
- API Docs: http://localhost:8173/docs

### Production

```bash
# 1. Build and run
cd docker
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. Or run directly
cd backend
cp ../.env.prod .env
uv sync --no-dev
uv run alembic upgrade head
uv run uvicorn farseer.main:app --host 0.0.0.0 --port 8174
```

Access:
- API: http://localhost:8174
- API Docs: http://localhost:8174/docs

### Nginx (Optional)

For reverse proxy with `/farseer` routing:

```bash
# Copy nginx config
sudo cp docker/nginx/farseer.conf /etc/nginx/conf.d/
sudo nginx -t && sudo systemctl reload nginx
```

Then access:
- Production: http://your-server/farseer/
- Development: http://your-server/farseer/dev/

## Data Sources

| Source | Markets | OHLC | Fundamentals | Timeframes (Free) |
|--------|---------|------|--------------|------------|
| **Tushare** | A-shares, ETFs | ✅ Full history | ✅ Income, Balance, Indicators | 1d, 1w, 1M (intraday requires paid) |
| **AKShare** | A-shares, ETFs | ✅ | ✅ | 5m, 15m, 30m, 1h, 1d, 1w, 1M |
| **Baostock** | A-shares | ✅ Full history | ✅ Basic | 5m, 15m, 30m, 1h, 1d, 1w, 1M |
| **Yahoo Finance** | Global stocks, ETFs | ✅ | ✅ Basic | 1m, 2m, 5m, 15m, 30m, 1h, 90m, 1d, 1w, 1M |
| **Binance** | Crypto | ✅ Full history | ✅ Market data | All (1m to 1M) |

### OHLC Timeframes

| Timeframe | Code | Duration | Best For | Free Sources |
|-----------|------|----------|----------|-------------|
| 1 minute | `1m` | 1 min | Scalping, HFT | Yahoo (7d), Binance (full) |
| 3 minutes | `3m` | 3 min | Short-term trading | Binance (full) |
| 5 minutes | `5m` | 5 min | Day trading | AKShare, Baostock, Yahoo (60d), Binance (full) |
| 15 minutes | `15m` | 15 min | Day trading | AKShare, Baostock, Yahoo (60d), Binance (full) |
| 30 minutes | `30m` | 30 min | Swing trading | AKShare, Baostock, Yahoo (60d), Binance (full) |
| 1 hour | `1h` | 1 hr | Swing trading | AKShare, Baostock, Yahoo (730d), Binance (full) |
| 2 hours | `2h` | 2 hr | Position trading | Binance (full) |
| 4 hours | `4h` | 4 hr | Position trading | Binance (full) |
| 6 hours | `6h` | 6 hr | Position trading | Binance (full) |
| 8 hours | `8h` | 8 hr | Position trading | Binance (full) |
| 12 hours | `12h` | 12 hr | Position trading | Binance (full) |
| Daily | `1d` | 1 day | Long-term investing | All sources (full) |
| 3 days | `3d` | 3 days | Long-term investing | Binance (full) |
| Weekly | `1w` | 1 week | Long-term investing | All sources (full) |
| Monthly | `1M` | 1 month | Portfolio analysis | All sources (full) |

See [docs/TIMEFRAMES.md](docs/TIMEFRAMES.md) for detailed coverage by source.

## Branch Strategy

- `master` - Production-ready code
- `dev` - Development branch

## Project Structure

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Design Decisions

See [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md)
