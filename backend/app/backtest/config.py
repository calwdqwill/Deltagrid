"""Backtest configuration and core data models."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run."""

    strategy_type: str  # "funding_mean_reversion" | "basis_compression" | "liquidation_cascade_fade"
    symbol: str  # "BTC" | "ETH" | "SOL" | "HYPE"
    exchange: str  # "binance" | "bybit" | "okx" | "hyperliquid"
    start_ms: int  # unix timestamp ms
    end_ms: int  # unix timestamp ms
    position_size_usd: float = 10_000.0
    leverage: float = 1.0
    fee_type: str = "taker"  # "maker" | "taker"
    use_slippage: bool = True
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Current position state."""

    side: str = "flat"  # "long" | "short" | "flat"
    entry_price: float = 0.0
    size_usd: float = 0.0
    entry_time_ms: int = 0
    funding_pnl: float = 0.0  # cumulative funding PnL
    fees_paid: float = 0.0  # cumulative fees
    slippage_paid: float = 0.0  # cumulative slippage


@dataclass
class Trade:
    """Completed trade record."""

    entry_time_ms: int = 0
    exit_time_ms: int = 0
    symbol: str = ""
    exchange: str = ""
    side: str = ""  # "long" | "short"
    entry_price: float = 0.0
    exit_price: float = 0.0
    size_usd: float = 0.0
    price_pnl: float = 0.0  # (exit - entry) * size * direction
    funding_pnl: float = 0.0  # sum of funding payments
    fees: float = 0.0  # entry_fee + exit_fee
    slippage: float = 0.0  # entry_slippage + exit_slippage
    net_pnl: float = 0.0  # price_pnl + funding_pnl - fees - slippage
    hold_duration_min: int = 0
    exit_reason: str = ""  # "mean_reversion" | "time_based" | "stop_loss" | "take_profit" | "basis_compression"


@dataclass
class EquityPoint:
    """Single point on the equity curve."""

    timestamp_ms: int = 0
    equity: float = 0.0  # running total equity
    drawdown: float = 0.0  # peak-to-trough drawdown in USD
    drawdown_pct: float = 0.0  # drawdown as percentage
