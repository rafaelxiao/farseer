# Farseer

Market data server for OHLC, fundamentals, and more.

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Bun](https://bun.sh)
- Docker (for database)

### Development

```bash
# 1. Clone and checkout dev branch
git clone <repo-url>
cd farseer
git checkout dev

# 2. Start database
cd docker
docker compose up -d db
cd ..

# 3. Setup backend
cd backend
cp ../.env.dev .env
uv sync
uv run alembic upgrade head
uv run uvicorn farseer.main:app --reload --host 0.0.0.0

# 4. Setup frontend (new terminal)
cd frontend
bun install
bun dev --host
```

Access:
- Frontend: http://localhost:5173 (or http://<your-ip>:5173)
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Production

```bash
# 1. Build and run with Docker
cd docker
cp ../.env.prod ../backend/.env
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. Or run backend directly
cd backend
cp ../.env.prod .env
uv sync --no-dev
uv run alembic upgrade head
uv run uvicorn farseer.main:app --host 0.0.0.0 --port 8000
```

## Branch Strategy

- `master` - Production-ready code
- `dev` - Development branch, merge to master when stable

## Project Structure

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Design Decisions

See [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| ENVIRONMENT | `dev` or `prod` | `dev` |
| DEBUG | Enable debug mode | `true` |
| DATABASE_URL | Async PostgreSQL URL | postgresql+asyncpg://... |
| DATABASE_URL_SYNC | Sync PostgreSQL URL | postgresql+psycopg2://... |
| HOST | Server host | `0.0.0.0` |
| PORT | Server port | `8000` |
| CORS_ORIGINS | Allowed CORS origins | `["http://localhost:5173"]` |
