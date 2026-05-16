"""Pydantic schemas for RWA (Real World Assets) domain."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RwaAssetSnapshotSchema(BaseModel):
    id: str
    asset_id: str
    source: str
    source_quality: str = "verified"
    price_usd: Optional[float] = None
    nav_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    total_supply: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    yield_apr: Optional[float] = None
    premium_discount_pct: Optional[float] = None
    fetched_at: datetime
    next_expected_update_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RwaAssetSchema(BaseModel):
    id: str
    symbol: str
    name: str
    category: str
    asset_class: str = "rwa"
    issuer: Optional[str] = None
    blockchain: Optional[str] = None
    contract_address: Optional[str] = None
    decimals: Optional[int] = None
    is_active: bool = True
    is_executable: bool = False
    latest_snapshot: Optional[RwaAssetSnapshotSchema] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RwaCategorySchema(BaseModel):
    category: str
    count: int


class RwaCompareSchema(BaseModel):
    asset_a: RwaAssetSchema
    asset_b: RwaAssetSchema
    diff_price_pct: Optional[float] = None
    diff_nav_pct: Optional[float] = None
    notes: str = ""


class RwaAssetListResponse(BaseModel):
    data: list[RwaAssetSchema]
    meta: dict = Field(default_factory=dict)
