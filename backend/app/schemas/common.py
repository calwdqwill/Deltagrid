from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class DataStatus(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    STALE = "stale"
    FALLBACK = "fallback"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class ApiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    data: Any
    meta: dict = {}


class DataSourceStatus(BaseModel):
    source: str
    status: str  # "ok", "degraded", "down"
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    records_fetched: int = 0
    latency_ms: Optional[float] = None
