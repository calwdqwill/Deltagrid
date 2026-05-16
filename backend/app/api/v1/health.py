from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse, DataSourceStatus
from app.adapters.registry import create_default_registry
from app.config import get_settings
from app.services.cache_service import InMemoryCacheService
from app.services.providers.provider_health_service import ProviderHealthService
from app.core.dependencies import get_db

router = APIRouter(prefix="/health", tags=["health"])


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
