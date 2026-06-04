"""Database URL normalization helpers."""


def normalize_postgres_alias(database_url: str) -> str:
    """Normalize provider aliases such as postgres:// to SQLAlchemy's postgresql://."""
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def to_sync_database_url(database_url: str) -> str:
    """Return a sync SQLAlchemy URL for the configured database."""
    normalized = normalize_postgres_alias(database_url)
    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+psycopg://", 1)
    if normalized.startswith("postgresql+asyncpg://"):
        return normalized.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    return normalized


def to_async_database_url(database_url: str) -> str:
    """Return an async SQLAlchemy URL for the configured database."""
    normalized = normalize_postgres_alias(database_url)
    if normalized.startswith("sqlite://"):
        return normalized.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+asyncpg://", 1)
    if normalized.startswith("postgresql+psycopg://"):
        return normalized.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    return normalized


def is_sqlite_database_url(database_url: str) -> bool:
    """Return True when the configured URL targets SQLite."""
    normalized = database_url.strip().lower()
    return normalized.startswith("sqlite://") or normalized.startswith("sqlite+aiosqlite://")
