from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExchangeAccountCreate(BaseModel):
    exchange_name: str = Field(..., min_length=1)
    account_label: str = Field(default="Main", min_length=1)
    account_type: str = Field(default="spot")


class ExchangeAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    exchange_name: str
    account_label: str
    account_type: str
    is_active: bool
    is_default: bool
    has_keys: bool = False
    created_at: datetime
    updated_at: datetime


class ExchangeKeyStoreRequest(BaseModel):
    api_key: str = Field(..., min_length=1)
    api_secret: str = Field(..., min_length=1)
    passphrase: Optional[str] = None
    is_testnet: bool = False


class ConnectorCapabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exchange_name: str
    supports_spot: bool
    supports_perp: bool
    supports_margin: bool
    supports_market_order: bool
    supports_limit_order: bool
    supports_stop_loss: bool
    supports_cancel: bool
    supports_ws: bool
    rate_limit_requests_per_minute: int
