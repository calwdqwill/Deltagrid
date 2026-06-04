from datetime import datetime
from functools import lru_cache
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse, DataSourceStatus
from app.adapters.registry import create_default_registry
from app.config import get_settings
from app.services.cache_service import InMemoryCacheService
from app.services.providers.provider_health_service import ProviderHealthService
from app.core.dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def _expected_migration_heads() -> tuple[str, ...]:
    config = Config(str(_backend_root() / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(_backend_root() / "app" / "persistence" / "migrations"),
    )
    script = ScriptDirectory.from_config(config)
    return tuple(script.get_heads())


@router.get("")
async def health_check():
    """@public_ready — Health check endpoint. Safe for external monitoring."""
    return ApiResponse(data={
        "status": "healthy",
        "version": get_settings().app_version,
        "api_version": "v1",
        "api_tier": "internal",
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.get("/readiness", response_model=ApiResponse)
async def readiness_check(response: Response, db: Session = Depends(get_db)):
    """@public_ready — Local readiness check for DB connectivity and migrations."""
    database_ok = False
    database_error = None
    current_revision = None
    migration_error = None
    expected_heads: tuple[str, ...] = ()

    try:
        db.execute(text("SELECT 1")).scalar_one()
        database_ok = True
    except SQLAlchemyError as exc:
        database_error = str(exc.__class__.__name__)

    try:
        expected_heads = _expected_migration_heads()
    except Exception as exc:
        migration_error = f"source_head_unavailable:{exc.__class__.__name__}"

    if database_ok:
        try:
            row = db.execute(text("SELECT version_num FROM alembic_version")).first()
            current_revision = row[0] if row else None
        except SQLAlchemyError as exc:
            migration_error = str(exc.__class__.__name__)

    migrations_ok = bool(current_revision and current_revision in expected_heads)
    ready = database_ok and migrations_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ApiResponse(
        data={
            "status": "ready" if ready else "not_ready",
            "checks": {
                "database": {
                    "ok": database_ok,
                    "error": database_error,
                },
                "migrations": {
                    "ok": migrations_ok,
                    "current_revision": current_revision,
                    "expected_heads": list(expected_heads),
                    "error": migration_error,
                },
            },
        },
        meta={
            "timestamp": datetime.utcnow().isoformat(),
            "read_only": True,
        },
    )


@router.get("/status")
async def data_status():
    registry = create_default_registry(get_settings().coingecko_api_key)
    adapter_health = await registry.health_check_all()
    cache = InMemoryCacheService()
    cache_info = await cache.info()

    sources = []
    for name, health in adapter_health.items():
        sources.append(DataSourceStatus(
            source=name,
            status=health.get("status", "unknown"),
            last_success=datetime.fromisoformat(health["last_success"]) if health.get("last_success") else None,
            last_error=health.get("last_error"),
            records_fetched=health.get("records_fetched", 0),
        ))

    return ApiResponse(data={
        "sources": [s.model_dump() for s in sources],
        "cache": cache_info,
        "timestamp": datetime.utcnow().isoformat(),
    })


@router.get("/providers", response_model=ApiResponse)
async def provider_health(
    db: Session = Depends(get_db),
):
    service = ProviderHealthService(db)
    health = service.get_health()
    return ApiResponse(data=health)
