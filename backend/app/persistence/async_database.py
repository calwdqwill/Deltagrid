"""Async database engine for services that need async SQLAlchemy sessions."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.persistence.database_url import is_sqlite_database_url, to_async_database_url

settings = get_settings()


async_engine = create_async_engine(
    to_async_database_url(settings.database_url),
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_db():
    """Yield an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_async_db() -> None:
    """Create SQLite fallback tables using the async engine."""
    if not is_sqlite_database_url(str(async_engine.url)):
        return
    from app.domain.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
