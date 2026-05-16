from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import DataStatus


class ScannerRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    token_name: str
    symbol: str
    pair: str
    icon_url: Optional[str] = None
    scanner_type: str
    buy_venue: str
    buy_price: float = Field(..., ge=0)
    sell_venue: str
    sell_price: float = Field(..., ge=0)
    spread_pct: float
    net_profit_pct: float
    volume_24h: Optional[float] = None
    signal: str
    trend_series: list[float] = []
    data_status: DataStatus
    source_label: str
    updated_at: datetime
    is_favorite: bool = False
    is_pinned: bool = False
    basis_pct: Optional[float] = None
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None
    strategy_hint: Optional[str] = None

    def computed_spread(self) -> float:
        if self.buy_price == 0:
            return 0.0
        return ((self.sell_price - self.buy_price) / self.buy_price) * 100


class ScannerMeta(BaseModel):
    total: int
    filtered: int
    data_status_counts: dict = {}
    last_updated: Optional[datetime] = None
    sources: list[str] = []
    is_fallback: bool = False


class ScannerListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    records: list[ScannerRecord]
    meta: ScannerMeta


class ScannerDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    record: ScannerRecord
