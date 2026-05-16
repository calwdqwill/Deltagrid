from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PerformanceSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    max_drawdown_pct: Optional[float]
    sharpe_ratio: Optional[float]
    win_rate_pct: Optional[float]
    snapshot_at: datetime


class PnLSummary(BaseModel):
    total_pnl: float
    total_pnl_pct: float
    avg_trade_pnl: float
    best_trade_pnl: float
    worst_trade_pnl: float


class WinRateMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: Optional[float]


class DrawdownMetrics(BaseModel):
    max_drawdown_pct: Optional[float]
    max_drawdown_amount: Optional[float]
    current_drawdown_pct: Optional[float]


class SharpeMetrics(BaseModel):
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    volatility_pct: Optional[float]
    annualized_return_pct: Optional[float]


class PerformanceMetrics(BaseModel):
    pnl: PnLSummary
    win_rate: WinRateMetrics
    drawdown: DrawdownMetrics
    sharpe: SharpeMetrics
