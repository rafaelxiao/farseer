# Farseer - Design Decisions

## Project

Centralized server for market data. OHLC (multi-timeframe), fundamentals, future: tick data, alternative data, media.

Features:
- API to read and write data
- Data fetchers (pull from multiple sources into DB)
- Task runner to schedule/perform fetch jobs
- Frontend for data preview and task management

---

## Decisions

### 2026-06-09 — Backend

| Decision | Choice |
|----------|--------|
| Database | PostgreSQL + TimescaleDB |
| Backend | Python + FastAPI |
| ORM | SQLAlchemy 2.x |
| DB Driver | psycopg2 (sync) / asyncpg (async) |
| Env/Package Manager | uv |
| Task Scheduling | APScheduler |

### 2026-06-09 — Frontend

| Decision | Choice |
|----------|--------|
| Framework | React + TypeScript |
| UI Components | shadcn/ui |
| Build Tool | Vite |
| Package Manager | Bun |
| Server State | TanStack Query |

### 2026-06-09 — Symbol System

| Decision | Choice |
|----------|--------|
| Format | `{CODE}.{EXCHANGE}` (e.g. `600519.SH`) |
| Exchanges | `.SH` (Shanghai), `.SZ` (Shenzhen), `.HK` (Hong Kong), `.US` (optional) |
| Conversion | Each source has converter for its format |

### 2026-06-09 — Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| yfinance | ✅ Implemented | US, HK, A-shares (.SS/.SZ) |
| baostock | ✅ Implemented | Free A-share data |
| tushare | Planned | Popular, rate-limited free tier |

---

## Tech Stack

### Backend

| Layer | Choice | Version |
|-------|--------|---------|
| Database | PostgreSQL + TimescaleDB | PG 16 + Latest |
| API | Python + FastAPI | 3.11+ |
| ORM | SQLAlchemy | 2.x |
| DB Driver | psycopg2 (sync) / asyncpg (async) | Latest |
| Env/Package Manager | uv | Latest |
| Task Scheduling | APScheduler | 3.x |

### Frontend

| Layer | Choice | Version |
|-------|--------|---------|
| Framework | React + TypeScript | Latest |
| UI Components | shadcn/ui | Latest |
| Build Tool | Vite | Latest |
| Package Manager | Bun | Latest |
| Server State | TanStack Query | Latest |
