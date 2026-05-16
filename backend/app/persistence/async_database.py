"""Async PostgreSQL database engine for Phase 2.

Coexists with the existing sync SQLite engine (database.py).
Switchover is controlled via DATABASE_URL env var.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings

settings = get_settings()

# Async engine for PostgreSQL (or aiosqlite for async SQLite)
async_engine = create_async_engine(
    settings.database_url,
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
    """Create tables using async engine (for dev convenience)."""
    from app.domain.models import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
