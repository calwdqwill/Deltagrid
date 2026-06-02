"""Backtest metrics calculation and result container."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from app.backtest.config import EquityPoint, Trade


@dataclass
class BacktestResult:
    """Complete backtest result with all metrics."""

    # Meta
    strategy_type: str = ""
    symbol: str = ""
    exchange: str = ""
    start_ms: int = 0
    end_ms: int = 0
    total_bars: int = 0
    data_coverage: float = 0.0  # % of bars with complete data

    # Returns
    total_return_pct: float = 0.0  # total return in %
    cagr_pct: float = 0.0  # compound annual growth rate

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0  # CAGR / max drawdown

    # Drawdown
    max_drawdown_pct: float = 0.0
    max_drawdown_duration_ms: int = 0  # longest drawdown in ms

    # Trade stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0  # %
    profit_factor: float = 0.0  # gross profit / gross loss
    avg_trade_pnl: float = 0.0  # USD
    median_trade_pnl: float = 0.0  # USD
    avg_win: float = 0.0  # USD
    avg_loss: float = 0.0  # USD
    best_trade: float = 0.0  # USD
    worst_trade: float = 0.0  # USD

    # Time
    exposure_time_pct: float = 0.0  # % of time in market
    avg_hold_time_min: float = 0.0
    median_hold_time_min: float = 0.0

    # PnL Decomposition (all in % of initial equity)
    price_pnl_pct: float = 0.0  # from price movement
    funding_pnl_pct: float = 0.0  # from funding payments
    fees_drag_pct: float = 0.0  # negative (cost)
    slippage_drag_pct: float = 0.0  # negative (cost)
    net_pnl_pct: float = 0.0  # total after all costs

    # Detailed data
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[EquityPoint] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes to dict for JSON response."""

        def _clean(val):
            """Convert numpy types to native Python types."""
            if hasattr(val, "item"):  # numpy scalar
                return val.item()
            return val

        return {
            "meta": {
                "strategy_type": self.strategy_type,
                "symbol": self.symbol,
                "exchange": self.exchange,
                "start_ms": _clean(self.start_ms),
                "end_ms": _clean(self.end_ms),
                "total_bars": _clean(self.total_bars),
                "data_coverage": round(float(self.data_coverage), 4),
            },
            "returns": {
                "total_return_pct": round(float(self.total_return_pct), 4),
                "cagr_pct": round(float(self.cagr_pct), 4),
            },
            "risk_adjusted": {
                "sharpe_ratio": round(float(self.sharpe_ratio), 4),
                "sortino_ratio": round(float(self.sortino_ratio), 4),
                "calmar_ratio": round(float(self.calmar_ratio), 4),
            },
            "drawdown": {
                "max_drawdown_pct": round(float(self.max_drawdown_pct), 4),
                "max_drawdown_duration_ms": _clean(self.max_drawdown_duration_ms),
            },
            "trade_stats": {
                "total_trades": _clean(self.total_trades),
                "winning_trades": _clean(self.winning_trades),
                "losing_trades": _clean(self.losing_trades),
                "win_rate": round(float(self.win_rate), 4),
                "profit_factor": round(float(self.profit_factor), 4),
                "avg_trade_pnl": round(float(self.avg_trade_pnl), 4),
                "median_trade_pnl": round(float(self.median_trade_pnl), 4),
                "avg_win": round(float(self.avg_win), 4),
                "avg_loss": round(float(self.avg_loss), 4),
                "best_trade": round(float(self.best_trade), 4),
                "worst_trade": round(float(self.worst_trade), 4),
            },
            "time": {
                "exposure_time_pct": round(float(self.exposure_time_pct), 4),
                "avg_hold_time_min": round(float(self.avg_hold_time_min), 4),
                "median_hold_time_min": round(float(self.median_hold_time_min), 4),
            },
            "pnl_decomposition": {
                "price_pnl_pct": round(float(self.price_pnl_pct), 4),
                "funding_pnl_pct": round(float(self.funding_pnl_pct), 4),
                "fees_drag_pct": round(float(self.fees_drag_pct), 4),
                "slippage_drag_pct": round(float(self.slippage_drag_pct), 4),
                "net_pnl_pct": round(float(self.net_pnl_pct), 4),
            },
            "trades": [
                {
                    "entry_time_ms": _clean(t.entry_time_ms),
                    "exit_time_ms": _clean(t.exit_time_ms),
                    "symbol": t.symbol,
                    "exchange": t.exchange,
                    "side": t.side,
                    "entry_price": round(float(t.entry_price), 8),
                    "exit_price": round(float(t.exit_price), 8),
                    "size_usd": round(float(t.size_usd), 4),
                    "price_pnl": round(float(t.price_pnl), 4),
                    "funding_pnl": round(float(t.funding_pnl), 4),
                    "fees": round(float(t.fees), 4),
                    "slippage": round(float(t.slippage), 4),
                    "net_pnl": round(float(t.net_pnl), 4),
                    "hold_duration_min": _clean(t.hold_duration_min),
                    "exit_reason": t.exit_reason,
                }
                for t in self.trades
            ],
            "equity_curve": [
                {
                    "timestamp_ms": _clean(e.timestamp_ms),
                    "equity": round(float(e.equity), 4),
                    "drawdown": round(float(e.drawdown), 4),
                    "drawdown_pct": round(float(e.drawdown_pct), 4),
                }
                for e in self.equity_curve
            ],
        }

    def summary(self) -> str:
        """Returns human-readable summary string."""
        lines = [
            "=" * 60,
            f"Backtest Result: {self.strategy_type} | {self.symbol}/{self.exchange}",
            f"Period: {self.start_ms} -> {self.end_ms} | Bars: {self.total_bars}",
            "-" * 60,
            f"Total Return:     {self.total_return_pct:+.2f}%",
            f"CAGR:             {self.cagr_pct:+.2f}%",
            f"Sharpe Ratio:     {self.sharpe_ratio:.2f}",
            f"Sortino Ratio:    {self.sortino_ratio:.2f}",
            f"Calmar Ratio:     {self.calmar_ratio:.2f}",
            f"Max Drawdown:     {self.max_drawdown_pct:.2f}%",
            f"Max DD Duration:  {self.max_drawdown_duration_ms // 86400000}d",
            "-" * 60,
            f"Total Trades:     {self.total_trades}",
            f"Win Rate:         {self.win_rate:.1f}%",
            f"Profit Factor:    {self.profit_factor:.2f}",
            f"Avg Trade PnL:    ${self.avg_trade_pnl:+.2f}",
            f"Best Trade:       ${self.best_trade:+.2f}",
            f"Worst Trade:      ${self.worst_trade:+.2f}",
            f"Avg Win:          ${self.avg_win:+.2f}",
            f"Avg Loss:         ${self.avg_loss:+.2f}",
            "-" * 60,
            f"Exposure Time:    {self.exposure_time_pct:.1f}%",
            f"Avg Hold Time:    {self.avg_hold_time_min:.0f} min",
            "-" * 60,
            f"Price PnL:        {self.price_pnl_pct:+.2f}%",
            f"Funding PnL:      {self.funding_pnl_pct:+.2f}%",
            f"Fees Drag:        {self.fees_drag_pct:+.2f}%",
            f"Slippage Drag:    {self.slippage_drag_pct:+.2f}%",
            f"Net PnL:          {self.net_pnl_pct:+.2f}%",
            f"Data Coverage:    {self.data_coverage:.1f}%",
            "=" * 60,
        ]
        return "\n".join(lines)


def calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sharpe ratio from daily returns."""
    if returns.empty or returns.std() == 0:
        return 0.0
    # Annualize: daily mean * 365, daily std * sqrt(365)
    excess = returns - risk_free_rate / 365
    return float((excess.mean() / returns.std()) * np.sqrt(365))


def calculate_sortino(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Annualized Sortino ratio (downside deviation only)."""
    if returns.empty:
        return 0.0
    downside = returns[returns < 0]
    if downside.empty or downside.std() == 0:
        return 0.0
    excess = returns.mean() - risk_free_rate / 365
    return float((excess / downside.std()) * np.sqrt(365))


def calculate_drawdown(equity_series: pd.Series) -> Tuple[float, int]:
    """Returns (max_drawdown_pct, max_drawdown_duration_ms)."""
    if equity_series.empty:
        return 0.0, 0

    rolling_max = equity_series.cummax()
    drawdown = (equity_series - rolling_max) / rolling_max
    max_dd_pct = float(drawdown.min())

    # Find longest drawdown duration in milliseconds
    # A drawdown period starts when equity drops below peak and ends when it makes a new peak
    max_dd_duration_ms = 0
    peak_idx = 0
    in_drawdown = False

    # Get timestamps as array for duration calculation
    timestamps = equity_series.index
    for i in range(1, len(equity_series)):
        if equity_series.iloc[i] >= rolling_max.iloc[i]:
            # New peak — drawdown ended
            if in_drawdown:
                duration = timestamps[i] - timestamps[peak_idx]
                max_dd_duration_ms = max(max_dd_duration_ms, duration)
            peak_idx = i
            in_drawdown = False
        else:
            in_drawdown = True

    # If still in drawdown at end
    if in_drawdown:
        duration = timestamps[-1] - timestamps[peak_idx]
        max_dd_duration_ms = max(max_dd_duration_ms, duration)

    return max_dd_pct, max_dd_duration_ms


def decompose_pnl(trades: List[Trade], initial_equity: float) -> Dict[str, float]:
    """Decomposes total PnL into components as % of initial equity."""
    if initial_equity == 0 or not trades:
        return {
            "price_pnl": 0.0,
            "funding_pnl": 0.0,
            "fees": 0.0,
            "slippage": 0.0,
        }

    price_pnl = sum(t.price_pnl for t in trades)
    funding_pnl = sum(t.funding_pnl for t in trades)
    fees = sum(t.fees for t in trades)
    slippage = sum(t.slippage for t in trades)

    return {
        "price_pnl": (price_pnl / initial_equity) * 100,
        "funding_pnl": (funding_pnl / initial_equity) * 100,
        "fees": (fees / initial_equity) * 100,
        "slippage": (slippage / initial_equity) * 100,
    }
