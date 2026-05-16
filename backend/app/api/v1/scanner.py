from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Depends

from app.schemas.common import ApiResponse
from app.schemas.scanner import ScannerListResponse, ScannerDetailResponse
from app.services.cache_service import InMemoryCacheService, CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.perp_dex_service import PerpDEXService
from app.services.scanner_service import ScannerService
from app.services.preference_service import PreferenceService
from app.adapters.registry import create_default_registry
from app.config import get_settings
from app.core.dependencies import get_current_user_id, get_cache

router = APIRouter(prefix="/scanner", tags=["scanner"])

# Singleton registry and cache to avoid recreating adapters and losing cache on every request
_settings = get_settings()
_registry = create_default_registry(_settings.coingecko_api_key)
_cache = InMemoryCacheService(
    max_size=_settings.cache_max_size,
    default_ttl=_settings.cache_ttl_seconds,
)
_cg_service = CoinGeckoService(_registry.get("coingecko"))
_perp_service = PerpDEXService(_registry)


def get_scanner_service(user_id: Optional[str] = None, cache: Optional[CacheService] = None) -> tuple[ScannerService, PreferenceService]:
    pref_service = PreferenceService(user_id=user_id, cache=cache)
    scanner_service = ScannerService(_cache, _cg_service, _perp_service, pref_service)
    return scanner_service, pref_service


@router.get("", response_model=ApiResponse)
async def list_scanner(
    type: Optional[str] = Query(None, description="Filter by scanner type: cex-cex, dex-cex, spot-perp"),
    min_spread: Optional[float] = Query(None, ge=0, le=100),
    min_volume: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None),
    positive_net_only: bool = Query(False),
    user_id: Optional[str] = Depends(get_current_user_id),
    cache: CacheService = Depends(get_cache),
):
    service, pref_service = get_scanner_service(user_id=user_id, cache=cache)
    try:
        result = await service.fetch_all()

        records = result.records

        if type and type != "all":
            records = [r for r in records if r.scanner_type == type]
        if min_spread is not None:
            records = [r for r in records if r.spread_pct >= min_spread]
        if min_volume is not None:
            records = [r for r in records if (r.volume_24h or 0) >= min_volume]
        if search:
            search_lower = search.lower()
            records = [
                r for r in records
                if search_lower in r.symbol.lower()
                or search_lower in r.token_name.lower()
                or search_lower in r.pair.lower()
            ]
        if positive_net_only:
            records = [r for r in records if r.net_profit_pct > 0]

        result.records = records
        result.meta.filtered = len(records)

        return ApiResponse(data=result)
    finally:
        pref_service.close()


@router.get("/{record_id}", response_model=ApiResponse)
async def get_scanner_detail(
    record_id: str,
    user_id: Optional[str] = Depends(get_current_user_id),
    cache: CacheService = Depends(get_cache),
):
    service, pref_service = get_scanner_service(user_id=user_id, cache=cache)
    try:
        record = await service.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Scanner record not found")
        return ApiResponse(data=ScannerDetailResponse(record=record))
    finally:
        pref_service.close()
