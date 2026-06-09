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

## Branch Strategy

- `master` - Production-ready code
- `dev` - Development branch

## Project Structure

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## Design Decisions

See [docs/DESIGN_DECISIONS.md](docs/DESIGN_DECISIONS.md)
