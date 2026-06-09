from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from farseer.api.v1.router import router as v1_router
from farseer.config import settings
from farseer.scheduler.runner import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="Farseer",
    description="Market data server",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
    root_path=settings.root_path,
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(v1_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "debug": settings.debug,
    }
