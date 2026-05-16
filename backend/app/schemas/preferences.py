from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ScannerPreferences(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    language: str = "en"
    min_spread_pct: float = Field(default=0.1, ge=0, le=100)
    min_volume_24h: Optional[float] = Field(default=None, ge=0)
    refresh_interval_sec: int = Field(default=60, ge=10, le=3600)
    slippage_pct: float = Field(default=0.0, ge=0, le=100)
    fee_buy_pct: float = Field(default=0.1, ge=0, le=100)
    fee_sell_pct: float = Field(default=0.1, ge=0, le=100)
    positive_net_only: bool = False
    selected_types: list[str] = ["cex-cex", "dex-cex", "spot-perp"]


class PreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    value: str
    updated_at: Optional[str] = None


class FavoritesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_ids: list[str]


class PinnedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instrument_ids: list[str]
