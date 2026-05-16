from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TrendingCoin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    symbol: str
    market_cap_rank: Optional[int] = None
    thumb: Optional[str] = None
    price_btc: Optional[float] = None
    score: int = 0


class TrendingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coins: list[TrendingCoin]


class MarketCoin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    symbol: str
    image: Optional[str] = None
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    market_cap_rank: Optional[int] = None
    price_change_percentage_24h: Optional[float] = None
    total_volume: Optional[float] = None


class GlobalData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_market_cap_usd: float = 0.0
    total_volume_24h_usd: float = 0.0
    btc_dominance: float = 0.0
    eth_dominance: float = 0.0
    active_cryptocurrencies: int = 0
    updated_at: Optional[datetime] = None
