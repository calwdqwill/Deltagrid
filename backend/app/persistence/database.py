from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.domain.models import Base
from app.persistence.database_url import is_sqlite_database_url, to_sync_database_url

settings = get_settings()


def create_database_engine(database_url: str) -> Engine:
    """Create the sync SQLAlchemy engine used by FastAPI dependencies."""
    sync_url = to_sync_database_url(database_url)
    engine_kwargs = {"echo": settings.debug}

    if is_sqlite_database_url(sync_url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_size"] = settings.database_pool_size
        engine_kwargs["max_overflow"] = settings.database_max_overflow
        engine_kwargs["pool_timeout"] = settings.database_pool_timeout_seconds

    return create_engine(sync_url, **engine_kwargs)


engine = create_database_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    if is_sqlite_database_url(str(engine.url)):
        Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
