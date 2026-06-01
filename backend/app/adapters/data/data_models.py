"""Canonical Data Format — Pydantic models for normalized market data.

All data adapters return these models regardless of the source exchange.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OHLCVCandle(BaseModel):
    """Normalized OHLCV candle."""

    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: Optional[float] = None
    trades_count: Optional[int] = None
    symbol: str          # canonical symbol, e.g. "BTC"
    exchange: str        # "binance", "bybit", ...
    interval: str        # "1m", "5m", "1h", "1d"

    @property
    def timestamp_dt(self) -> datetime:
        return datetime.utcfromtimestamp(self.timestamp_ms / 1000)

    class Config:
        frozen = True


class FundingRate(BaseModel):
    """Normalized funding rate record."""

    timestamp_ms: int
    symbol: str
    exchange: str
    funding_rate: float
    next_funding_time_ms: Optional[int] = None
    interval: str = "8h"   # "1h" (Hyperliquid) | "8h" (Binance)

    class Config:
        frozen = True


class OpenInterest(BaseModel):
    """Normalized open interest record."""

    timestamp_ms: int
    symbol: str
    exchange: str
    interval: str
    oi_usd: Optional[float] = None
    oi_coins: Optional[float] = None

    class Config:
        frozen = True


class Liquidation(BaseModel):
    """Normalized liquidation record."""

    timestamp_ms: int
    symbol: str
    exchange: str
    side: Literal["long", "short"]
    quantity: float
    price: float
    value_usd: float

    class Config:
        frozen = True


class LongShortRatio(BaseModel):
    """Normalized long/short ratio record."""

    timestamp_ms: int
    symbol: str
    exchange: str
    interval: str
    long_ratio: float
    short_ratio: float
    long_account_ratio: Optional[float] = None
    short_account_ratio: Optional[float] = None

    class Config:
        frozen = True


class ProviderHealthStatus(BaseModel):
    """Health check response for a data provider."""

    source_name: str
    is_healthy: bool
    latency_ms: Optional[int] = None
    last_error: Optional[str] = None
    circuit_breaker_state: str = "closed"   # "closed" | "open" | "half_open"


class BackfillResult(BaseModel):
    """Result of a backfill operation."""

    total_fetched: int = 0
    total_inserted: int = 0
    gaps: list[tuple[int, int]] = Field(default_factory=list)   # (start_ms, end_ms)

    @property
    def total_gap_ms(self) -> int:
        return sum(end - start for start, end in self.gaps)

    @property
    def success_rate(self) -> float:
        if self.total_fetched == 0:
            return 0.0
        return (self.total_inserted / self.total_fetched) * 100
