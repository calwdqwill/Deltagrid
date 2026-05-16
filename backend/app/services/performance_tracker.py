"""Performance tracking service: PnL, win rate, drawdown, Sharpe-ready metrics.

Calculates metrics over paper trade history. No external dependencies.
"""

import math
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import PaperTrade, PerformanceSnapshot
from app.schemas.performance import (
    PerformanceMetrics,
    PnLSummary,
    WinRateMetrics,
    DrawdownMetrics,
    SharpeMetrics,
    PerformanceSnapshotResponse,
)


class PerformanceTracker:
    def __init__(self, db: Session):
        self.db = db

    def calculate_metrics(self, account_id: str) -> PerformanceMetrics:
        trades = self.db.query(PaperTrade).filter(
            PaperTrade.account_id == account_id,
            PaperTrade.status == "closed",
        ).all()

        if not trades:
            return PerformanceMetrics(
                pnl=PnLSummary(total_pnl=0, total_pnl_pct=0, avg_trade_pnl=0, best_trade_pnl=0, worst_trade_pnl=0),
                win_rate=WinRateMetrics(total_trades=0, winning_trades=0, losing_trades=0, win_rate_pct=0, avg_win_pct=0, avg_loss_pct=0, profit_factor=None),
                drawdown=DrawdownMetrics(max_drawdown_pct=None, max_drawdown_amount=None, current_drawdown_pct=None),
                sharpe=SharpeMetrics(sharpe_ratio=None, sortino_ratio=None, volatility_pct=None, annualized_return_pct=None),
            )

        pnls = [float(t.pnl or 0) for t in trades]
        winning = [p for p in pnls if p > 0]
        losing = [p for p in pnls if p < 0]

        total_pnl = sum(pnls)
        total_pnl_pct = (total_pnl / max(abs(sum(float(t.entry_price) * float(t.quantity) for t in trades)), 1)) * 100

        avg_win = sum(winning) / len(winning) if winning else 0
        avg_loss = sum(losing) / len(losing) if losing else 0
        profit_factor = abs(sum(winning) / sum(losing)) if losing and sum(losing) != 0 else None

        win_rate_pct = (len(winning) / len(trades)) * 100 if trades else 0

        # Drawdown calculation
        cumulative = 0
        peak = 0
        max_dd_pct = 0.0
        max_dd_amount = 0.0
        for p in pnls:
            cumulative += p
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd_amount:
                max_dd_amount = dd
                max_dd_pct = (dd / peak) * 100 if peak > 0 else 0

        # Sharpe-ready (requires risk-free rate, simplified here)
        returns = pnls
        avg_return = sum(returns) / len(returns) if returns else 0
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns) if returns else 0
        std_dev = math.sqrt(variance) if variance > 0 else 0
        sharpe = (avg_return / std_dev) if std_dev > 0 else None

        return PerformanceMetrics(
            pnl=PnLSummary(
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                avg_trade_pnl=avg_return,
                best_trade_pnl=max(pnls),
                worst_trade_pnl=min(pnls),
            ),
            win_rate=WinRateMetrics(
                total_trades=len(trades),
                winning_trades=len(winning),
                losing_trades=len(losing),
                win_rate_pct=win_rate_pct,
                avg_win_pct=avg_win,
                avg_loss_pct=avg_loss,
                profit_factor=profit_factor,
            ),
            drawdown=DrawdownMetrics(
                max_drawdown_pct=max_dd_pct if max_dd_pct > 0 else None,
                max_drawdown_amount=max_dd_amount if max_dd_amount > 0 else None,
                current_drawdown_pct=None,
            ),
            sharpe=SharpeMetrics(
                sharpe_ratio=sharpe,
                sortino_ratio=None,
                volatility_pct=(std_dev / abs(avg_return) * 100) if avg_return != 0 else None,
                annualized_return_pct=None,
            ),
        )

    def create_snapshot(self, account_id: str) -> PerformanceSnapshotResponse:
        metrics = self.calculate_metrics(account_id)
        snapshot = PerformanceSnapshot(
            account_id=account_id,
            total_trades=metrics.win_rate.total_trades,
            winning_trades=metrics.win_rate.winning_trades,
            losing_trades=metrics.win_rate.losing_trades,
            total_pnl=metrics.pnl.total_pnl,
            max_drawdown_pct=metrics.drawdown.max_drawdown_pct,
            sharpe_ratio=metrics.sharpe.sharpe_ratio,
            win_rate_pct=metrics.win_rate.win_rate_pct,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return PerformanceSnapshotResponse(
            id=snapshot.id,
            account_id=snapshot.account_id,
            total_trades=snapshot.total_trades,
            winning_trades=snapshot.winning_trades,
            losing_trades=snapshot.losing_trades,
            total_pnl=float(snapshot.total_pnl),
            max_drawdown_pct=float(snapshot.max_drawdown_pct) if snapshot.max_drawdown_pct else None,
            sharpe_ratio=float(snapshot.sharpe_ratio) if snapshot.sharpe_ratio else None,
            win_rate_pct=float(snapshot.win_rate_pct) if snapshot.win_rate_pct else None,
            snapshot_at=snapshot.snapshot_at,
        )

    def get_history(self, account_id: str, limit: int = 30) -> list[PerformanceSnapshotResponse]:
        snapshots = self.db.query(PerformanceSnapshot).filter(
            PerformanceSnapshot.account_id == account_id,
        ).order_by(PerformanceSnapshot.snapshot_at.desc()).limit(limit).all()
        return [
            PerformanceSnapshotResponse(
                id=s.id,
                account_id=s.account_id,
                total_trades=s.total_trades,
                winning_trades=s.winning_trades,
                losing_trades=s.losing_trades,
                total_pnl=float(s.total_pnl),
                max_drawdown_pct=float(s.max_drawdown_pct) if s.max_drawdown_pct else None,
                sharpe_ratio=float(s.sharpe_ratio) if s.sharpe_ratio else None,
                win_rate_pct=float(s.win_rate_pct) if s.win_rate_pct else None,
                snapshot_at=s.snapshot_at,
            )
            for s in snapshots
        ]
