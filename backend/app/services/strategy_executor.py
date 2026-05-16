"""Strategy executor for paper trading.

Phase 2: Simulation only. No real execution.
Strategies: Z-Score, Basis, Cross-exchange placeholders.
"""

from typing import Optional
from dataclasses import dataclass

from app.services.spread_calculator import SpreadCalculator, SpreadResult


@dataclass
class StrategySignal:
    strategy: str
    instrument_id: str
    side: str  # buy, sell, hold
    confidence: float  # 0.0 - 1.0
    entry_price: float
    suggested_quantity: float
    reason: str


class StrategyExecutor:
    """Evaluate strategies and generate signals for paper trading.

    No state — pure functions. State lives in PaperTradingService.
    """

    @staticmethod
    def evaluate_z_score(
        instrument_id: str,
        current_price: float,
        mean_price: float,
        std_dev: float,
        threshold: float = 2.0,
    ) -> StrategySignal:
        """Z-Score mean reversion strategy."""
        if std_dev == 0:
            return StrategySignal(
                strategy="z_score",
                instrument_id=instrument_id,
                side="hold",
                confidence=0.0,
                entry_price=current_price,
                suggested_quantity=0.0,
                reason="Insufficient volatility",
            )

        z_score = (current_price - mean_price) / std_dev
        if z_score > threshold:
            side = "sell"
            confidence = min(abs(z_score) / 3.0, 1.0)
            reason = f"Z-score {z_score:.2f} > threshold, mean reversion sell"
        elif z_score < -threshold:
            side = "buy"
            confidence = min(abs(z_score) / 3.0, 1.0)
            reason = f"Z-score {z_score:.2f} < -threshold, mean reversion buy"
        else:
            side = "hold"
            confidence = 0.0
            reason = f"Z-score {z_score:.2f} within normal range"

        return StrategySignal(
            strategy="z_score",
            instrument_id=instrument_id,
            side=side,
            confidence=confidence,
            entry_price=current_price,
            suggested_quantity=0.1,  # placeholder sizing
            reason=reason,
        )

    @staticmethod
    def evaluate_basis(
        instrument_id: str,
        spot_price: float,
        perp_price: float,
        threshold_pct: float = 0.5,
    ) -> StrategySignal:
        """Basis trade: buy spot, sell perp when basis is positive."""
        if spot_price <= 0:
            return StrategySignal(
                strategy="basis",
                instrument_id=instrument_id,
                side="hold",
                confidence=0.0,
                entry_price=spot_price,
                suggested_quantity=0.0,
                reason="Invalid spot price",
            )

        basis_pct = ((perp_price - spot_price) / spot_price) * 100
        if basis_pct > threshold_pct:
            side = "buy"
            confidence = min(basis_pct / 1.0, 1.0)
            reason = f"Basis {basis_pct:.2f}% > threshold, buy spot"
        elif basis_pct < -threshold_pct:
            side = "sell"
            confidence = min(abs(basis_pct) / 1.0, 1.0)
            reason = f"Basis {basis_pct:.2f}% < -threshold, sell spot"
        else:
            side = "hold"
            confidence = 0.0
            reason = f"Basis {basis_pct:.2f}% within normal range"

        return StrategySignal(
            strategy="basis",
            instrument_id=instrument_id,
            side=side,
            confidence=confidence,
            entry_price=spot_price,
            suggested_quantity=0.1,
            reason=reason,
        )

    @staticmethod
    def evaluate_cross_exchange(
        instrument_id: str,
        buy_price: float,
        sell_price: float,
        fee_buy_pct: float = 0.1,
        fee_sell_pct: float = 0.1,
        min_net_profit_pct: float = 0.2,
    ) -> StrategySignal:
        """Cross-exchange arbitrage signal."""
        spread = SpreadCalculator.calculate(
            buy_price=buy_price,
            sell_price=sell_price,
            fee_buy_pct=fee_buy_pct,
            fee_sell_pct=fee_sell_pct,
        )

        if spread.net_profit_pct > min_net_profit_pct:
            side = "buy"
            confidence = min(spread.net_profit_pct / 1.0, 1.0)
            reason = f"Net profit {spread.net_profit_pct:.2f}% > min threshold"
        else:
            side = "hold"
            confidence = 0.0
            reason = f"Net profit {spread.net_profit_pct:.2f}% below threshold"

        return StrategySignal(
            strategy="cross_exchange",
            instrument_id=instrument_id,
            side=side,
            confidence=confidence,
            entry_price=buy_price,
            suggested_quantity=0.1,
            reason=reason,
        )
