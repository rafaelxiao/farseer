from collections.abc import AsyncGenerator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from farseer.config import settings
from farseer.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def verify_api_key(request: Request):
    """Require X-API-Key header. Skips auth endpoints + docs."""
    path = request.url.path
    if path.startswith("/api/v1/auth/") or path in ("/docs", "/openapi.json", "/redoc"):
        return

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
