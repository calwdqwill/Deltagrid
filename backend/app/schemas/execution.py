from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderIntentCreate(BaseModel):
    account_id: str
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit|stop_loss|take_profit)$")
    quantity: float = Field(..., gt=0)
    price: Optional[float] = None
    strategy: Optional[str] = None


class OrderIntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    risk_check_result: Optional[dict] = None
    created_at: datetime


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    filled_quantity: float
    remaining_quantity: Optional[float]
    price: Optional[float]
    avg_fill_price: Optional[float]
    status: str
    fee_amount: Optional[float]
    fee_currency: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]
    filled_at: Optional[datetime]


class OrderEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    event_type: str
    from_status: Optional[str]
    to_status: Optional[str]
    payload_json: Optional[str]
    created_at: datetime


class ExecutionSessionCreate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    is_live: bool = False


class ExecutionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: Optional[str]
    strategy: Optional[str]
    status: str
    is_live: bool
    started_at: datetime
    stopped_at: Optional[datetime]
