from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PaperAccountCreate(BaseModel):
    name: Optional[str] = "Demo Account"
    initial_balance: float = Field(default=10000.0, ge=0)
    currency: str = "USDT"


class PaperAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    initial_balance: float
    current_balance: float
    currency: str
    is_active: bool
    created_at: datetime


class PaperTradeCreate(BaseModel):
    strategy: str
    instrument_id: str
    side: str  # buy, sell
    entry_price: float = Field(..., gt=0)
    quantity: float = Field(..., gt=0)
    fee_pct: float = Field(default=0.10, ge=0)
    slippage_pct: float = Field(default=0.0, ge=0)


class PaperTradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    strategy: str
    instrument_id: str
    side: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    status: str  # open, closed, cancelled
    pnl: Optional[float]
    pnl_pct: Optional[float]
    fee_pct: float
    slippage_pct: float
    opened_at: datetime
    closed_at: Optional[datetime]


class PortfolioState(BaseModel):
    account_id: str
    current_balance: float
    total_pnl: float
    open_trades: int
    closed_trades: int
    active_strategies: list[str]
