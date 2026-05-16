"""RWA (Real World Assets) API router."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.rwa.rwa_asset_service import RwaAssetService
from app.schemas.rwa import RwaAssetListResponse, RwaAssetSchema, RwaCategorySchema, RwaCompareSchema

router = APIRouter(prefix="/rwa", tags=["RWA"])


def get_rwa_service(db: Session = Depends(get_db)) -> RwaAssetService:
    return RwaAssetService(db)


@router.get("/assets", response_model=RwaAssetListResponse)
async def list_rwa_assets(
    category: Optional[str] = None,
    service: RwaAssetService = Depends(get_rwa_service),
):
    """List RWA assets with optional category filter."""
    assets = await service.list_assets(category=category)
    return RwaAssetListResponse(data=assets, meta={"count": len(assets)})


@router.get("/assets/{asset_id}", response_model=RwaAssetSchema)
async def get_rwa_asset(
    asset_id: str,
    service: RwaAssetService = Depends(get_rwa_service),
):
    """Get a single RWA asset with its latest snapshot."""
    asset = await service.get_asset_with_latest_snapshot(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="RWA asset not found")
    return RwaAssetSchema(**asset)


@router.get("/assets/{asset_id}/snapshots")
async def get_rwa_asset_snapshots(
    asset_id: str,
    limit: int = 30,
    service: RwaAssetService = Depends(get_rwa_service),
):
    """Get historical snapshots for an RWA asset."""
    return {"data": await service.get_snapshots(asset_id, limit=limit)}


@router.get("/categories")
async def list_rwa_categories(
    service: RwaAssetService = Depends(get_rwa_service),
):
    """List RWA categories with asset counts."""
    return {"data": await service.get_categories()}


@router.get("/compare")
async def compare_rwa_assets(
    a: str,
    b: str,
    service: RwaAssetService = Depends(get_rwa_service),
):
    """Compare two RWA assets (e.g. XAUT vs PAXG)."""
    # Look up by symbol
    assets = await service.list_assets()
    asset_a = next((x for x in assets if x["symbol"].upper() == a.upper()), None)
    asset_b = next((x for x in assets if x["symbol"].upper() == b.upper()), None)

    if not asset_a or not asset_b:
        raise HTTPException(status_code=404, detail="One or both assets not found")

    # Enrich with latest snapshot
    asset_a_full = await service.get_asset_with_latest_snapshot(asset_a["id"])
    asset_b_full = await service.get_asset_with_latest_snapshot(asset_b["id"])

    snap_a = asset_a_full.get("latest_snapshot") or {}
    snap_b = asset_b_full.get("latest_snapshot") or {}

    price_a = snap_a.get("price_usd")
    price_b = snap_b.get("price_usd")
    nav_a = snap_a.get("nav_usd")
    nav_b = snap_b.get("nav_usd")

    diff_price_pct = None
    if price_a and price_b and price_b != 0:
        diff_price_pct = round(((price_a - price_b) / price_b) * 100, 4)

    diff_nav_pct = None
    if nav_a and nav_b and nav_b != 0:
        diff_nav_pct = round(((nav_a - nav_b) / nav_b) * 100, 4)

    return {
        "asset_a": asset_a_full,
        "asset_b": asset_b_full,
        "diff_price_pct": diff_price_pct,
        "diff_nav_pct": diff_nav_pct,
        "notes": f"Comparison based on latest available data.",
    }
