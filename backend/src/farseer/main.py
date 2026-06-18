from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from farseer.api.v1.router import router as v1_router
from farseer.config import settings
from farseer.scheduler.runner import start_scheduler, shutdown_scheduler
from farseer.database import async_session_factory
from farseer.services.auth import init_admin

# Import to register fetchers
import farseer.fetchers.sources  # noqa: F401


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key on all routes except auth + docs."""
    
    SKIP_PATTERNS = ("/auth/", "/docs", "/openapi.json", "/redoc", "/health")
    
    async def dispatch(self, request: Request, call_next):
        # Use scope path (root_path stripped) for reliable matching
        path = request.scope.get("path", request.url.path)
        if not any(p in path for p in self.SKIP_PATTERNS):
            if not settings.api_key:
                return await call_next(request)
            
            api_key = request.headers.get("X-API-Key")
            if api_key != settings.api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or missing X-API-Key header"}
                )
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with async_session_factory() as db:
        await init_admin(db)
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

# API Key auth (must be after CORS)
app.add_middleware(APIKeyMiddleware)

# Routes
app.include_router(v1_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "debug": settings.debug,
    }
