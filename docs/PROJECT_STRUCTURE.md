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
│   │       ├── main.py                  # FastAPI app, lifespan, middleware
│   │       ├── config.py                # Pydantic Settings
│   │       ├── database.py              # Engine, session factory, Base
│   │       │
│   │       ├── models/                  # SQLAlchemy models
│   │       │   ├── __init__.py
│   │       │   ├── base.py              # Timestamps, common mixins
│   │       │   ├── ohlc.py
│   │       │   ├── fundamentals.py
│   │       │   └── task.py              # Task/job records
│   │       │
│   │       ├── schemas/                 # Pydantic schemas
│   │       │   ├── __init__.py
│   │       │   ├── ohlc.py
│   │       │   ├── fundamentals.py
│   │       │   └── task.py
│   │       │
│   │       ├── api/                     # Route handlers
│   │       │   ├── __init__.py
│   │       │   ├── deps.py              # Shared dependencies (get_db)
│   │       │   └── v1/
│   │       │       ├── __init__.py
│   │       │       ├── router.py
│   │       │       ├── ohlc.py          # GET/POST OHLC data
│   │       │       ├── fundamentals.py  # GET/POST fundamentals
│   │       │       └── tasks.py         # GET tasks, POST trigger
│   │       │
│   │       ├── services/                # Business logic
│   │       │   ├── __init__.py
│   │       │   ├── ohlc.py
│   │       │   └── fundamentals.py
│   │       │
│   │       ├── fetchers/                # Data source fetchers
│   │       │   ├── __init__.py
│   │       │   ├── base.py              # Abstract base fetcher
│   │       │   └── example.py           # Example fetcher (Yahoo, etc.)
│   │       │
│   │       ├── scheduler/               # Task scheduling
│   │       │   ├── __init__.py
│   │       │   ├── runner.py            # APScheduler setup
│   │       │   └── jobs.py              # Job definitions
│   │       │
│   │       └── utils/
│   │           └── __init__.py
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── api/
│   │   │   └── v1/
│   │   └── services/
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   │
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── api/                         # API client
│   │   │   ├── client.ts
│   │   │   ├── ohlc.ts
│   │   │   ├── fundamentals.ts
│   │   │   └── tasks.ts
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                      # shadcn/ui
│   │   │   └── layout/                  # Shell, sidebar
│   │   │
│   │   ├── pages/                       # Route pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── OHLCViewer.tsx
│   │   │   ├── FundamentalsViewer.tsx
│   │   │   └── Tasks.tsx
│   │   │
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   │
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile.backend
│
├── .env.example
├── .gitignore
└── README.md
```

---

## Data Flow

```
                          ┌─────────────────┐
                          │   Data Sources   │
                          │  (Yahoo, APIs..) │
                          └────────┬────────┘
                                   │
                          fetchers/ │
                                   ▼
┌──────────┐    POST     ┌─────────────────┐    SQL     ┌─────────────┐
│ Frontend │ ──────────▶ │   FastAPI API    │ ────────▶ │ PostgreSQL  │
│ (React)  │ ◀────────── │   (api/v1/)      │ ◀──────── │ TimescaleDB │
└──────────┘    GET      └────────┬────────┘           └─────────────┘
                                   │
                          scheduler/│
                                   ▼
                          ┌─────────────────┐
                          │  APScheduler     │
                          │  (runs fetchers) │
                          └─────────────────┘
```

---

## Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| `models/` | DB table definitions |
| `schemas/` | Request/response validation |
| `api/` | HTTP routes, thin handlers |
| `services/` | Business logic, DB queries |
| `fetchers/` | Pull data from external sources |
| `scheduler/` | Cron-like job scheduling |

---

## Frontend Pages

| Page | Purpose |
|------|---------|
| Dashboard | Overview, quick stats |
| OHLC Viewer | Preview OHLC data with filters |
| Fundamentals Viewer | Preview fundamental data |
| Tasks | View scheduled jobs, run history, trigger manually |
