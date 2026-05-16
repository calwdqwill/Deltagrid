from app.constants import (
    SIGNAL_THRESHOLD_STRONG,
    SIGNAL_THRESHOLD_BUY_SELL,
    SIGNAL_THRESHOLD_MARGINAL,
    SignalLevel,
)


class SignalClassifier:
    """Rules-based signal classification.

    Classifies arbitrage opportunity based on net profit percentage.
    Explicit, transparent, not hardcoded per instrument.
    """

    @staticmethod
    def classify(net_profit_pct: float) -> str:
        if net_profit_pct >= SIGNAL_THRESHOLD_STRONG:
            return SignalLevel.STRONG
        elif net_profit_pct >= SIGNAL_THRESHOLD_BUY_SELL:
            return SignalLevel.BUY_SELL
        elif net_profit_pct >= SIGNAL_THRESHOLD_MARGINAL:
            return SignalLevel.MARGINAL
        else:
            return SignalLevel.HOLD

    @staticmethod
    def strategy_hint(net_profit_pct: float, scanner_type: str) -> str:
        type_label = scanner_type.value if hasattr(scanner_type, "value") else scanner_type
        if net_profit_pct >= SIGNAL_THRESHOLD_STRONG:
            return f"Strong {type_label} arbitrage opportunity"
        elif net_profit_pct >= SIGNAL_THRESHOLD_BUY_SELL:
            return f"Viable {type_label} opportunity"
        elif net_profit_pct >= SIGNAL_THRESHOLD_MARGINAL:
            return f"Marginal {type_label}, monitor closely"
        else:
            return "No actionable spread"
