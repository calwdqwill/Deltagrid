"""Pydantic schemas for Treasury Intelligence domain."""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, Field


class TreasurySnapshotSchema(BaseModel):
    id: str
    entity_id: str
    source: str
    source_quality: str = "verified"
    btc_holdings: Optional[float] = None
    btc_value_usd: Optional[float] = None
    total_treasury_usd: Optional[float] = None
    shares_outstanding: Optional[float] = None
    btc_per_share: Optional[float] = None
    report_date: Optional[date] = None
    fetched_at: datetime
    next_expected_update_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TreasuryEntitySchema(BaseModel):
    id: str
    entity_type: str
    name: str
    ticker: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool = True
    latest_snapshot: Optional[TreasurySnapshotSchema] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BtcHoldingsRowSchema(BaseModel):
    entity_id: str
    name: str
    ticker: Optional[str] = None
    btc_holdings: Optional[float] = None
    btc_value_usd: Optional[float] = None
    btc_per_share: Optional[float] = None
    report_date: Optional[str] = None
    source: str
    source_quality: str


class BtcHoldingsResponse(BaseModel):
    data: list[BtcHoldingsRowSchema]


class TokenizationPlatformSchema(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    tvl_usd: Optional[float] = None
    active_pools: Optional[int] = None
    blockchain: Optional[str] = None
    governance_token: Optional[str] = None
    is_active: bool = True
    last_updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
