"""Treasury Intelligence API router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.rwa.treasury_service import TreasuryService
from app.schemas.treasury import (
    TreasuryEntitySchema,
    BtcHoldingsResponse,
    TokenizationPlatformSchema,
)

router = APIRouter(prefix="/treasury", tags=["Treasury"])


def get_treasury_service(db: Session = Depends(get_db)) -> TreasuryService:
    return TreasuryService(db)


@router.get("/entities")
async def list_treasury_entities(
    entity_type: Optional[str] = None,
    service: TreasuryService = Depends(get_treasury_service),
):
    """List treasury entities (companies, platforms, issuers)."""
    return {"data": await service.list_entities(entity_type=entity_type)}


@router.get("/entities/{entity_id}")
async def get_treasury_entity(
    entity_id: str,
    service: TreasuryService = Depends(get_treasury_service),
):
    """Get a single treasury entity with its latest snapshot."""
    entity = await service.get_entity_with_latest_snapshot(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Treasury entity not found")
    return entity


@router.get("/entities/{entity_id}/snapshots")
async def get_treasury_snapshots(
    entity_id: str,
    limit: int = 30,
    service: TreasuryService = Depends(get_treasury_service),
):
    """Get historical snapshots for a treasury entity."""
    return {"data": await service.get_snapshots(entity_id, limit=limit)}


@router.get("/btc-holdings")
async def get_btc_holdings_leaderboard(
    limit: int = 50,
    service: TreasuryService = Depends(get_treasury_service),
):
    """Aggregated BTC treasury leaderboard."""
    return {"data": await service.get_btc_holdings_leaderboard(limit=limit)}


@router.get("/platforms")
async def list_tokenization_platforms(
    service: TreasuryService = Depends(get_treasury_service),
):
    """List tokenization platforms."""
    return {"data": await service.list_platforms()}
