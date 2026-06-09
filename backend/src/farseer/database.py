from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from farseer.config import settings

# Async engine (for FastAPI)
async_engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

# Sync engine (for migrations, scripts)
sync_engine = create_engine(settings.database_url_sync, echo=settings.debug)
sync_session_factory = sessionmaker(sync_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_sync_session() -> Session:
    return sync_session_factory()
