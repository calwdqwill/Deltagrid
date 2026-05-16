from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.preferences import ScannerPreferences, FavoritesResponse, PinnedResponse
from app.services.preference_service import PreferenceService
from app.core.dependencies import get_current_user_id, get_db, get_cache
from app.services.cache_service import CacheService

router = APIRouter(prefix="/preferences", tags=["preferences"])


def get_pref_service(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id),
    cache: CacheService = Depends(get_cache),
) -> PreferenceService:
    return PreferenceService(db=db, user_id=user_id, cache=cache)


@router.get("", response_model=ApiResponse)
async def get_preferences(service: PreferenceService = Depends(get_pref_service)):
    prefs = await service.get_scanner_preferences()
    return ApiResponse(data=prefs)


@router.post("", response_model=ApiResponse)
async def update_preferences(
    prefs: ScannerPreferences,
    service: PreferenceService = Depends(get_pref_service),
):
    updated = await service.update_preferences(prefs)
    return ApiResponse(data=updated)


@router.get("/favorites", response_model=ApiResponse)
async def get_favorites(service: PreferenceService = Depends(get_pref_service)):
    ids = await service.get_favorites()
    return ApiResponse(data=FavoritesResponse(instrument_ids=ids))


@router.post("/favorites/{instrument_id}", response_model=ApiResponse)
async def toggle_favorite(
    instrument_id: str,
    service: PreferenceService = Depends(get_pref_service),
):
    is_fav = await service.toggle_favorite(instrument_id)
    return ApiResponse(data={"instrument_id": instrument_id, "is_favorite": is_fav})


@router.get("/pinned", response_model=ApiResponse)
async def get_pinned(service: PreferenceService = Depends(get_pref_service)):
    ids = await service.get_pinned()
    return ApiResponse(data=PinnedResponse(instrument_ids=ids))


@router.post("/pinned/{instrument_id}", response_model=ApiResponse)
async def toggle_pinned(
    instrument_id: str,
    service: PreferenceService = Depends(get_pref_service),
):
    is_pinned = await service.toggle_pinned(instrument_id)
    return ApiResponse(data={"instrument_id": instrument_id, "is_pinned": is_pinned})
