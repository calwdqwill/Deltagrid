"""S01: Funding Rate Extreme Mean Reversion strategy.

Идея: funding rate — это плата за позицию. Когда funding экстремально высокий
(лонгеры переплачивают), открываем шорт. Когда экстремально низкий — лонг.
Edge основан на mean reversion: funding возвращается к среднему.
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from app.backtest.config import Position
from app.backtest.strategies.registry import BaseStrategy, register_strategy


@register_strategy("funding_mean_reversion")
class FundingMeanReversionStrategy(BaseStrategy):
    """S01: Funding Rate Extreme Mean Reversion."""

    DEFAULT_PARAMS = {
        "funding_long_threshold": -0.0001,   # -0.01% (10th percentile typical)
        "funding_short_threshold": 0.0003,    # +0.03% (90th percentile typical)
        "neutral_low": -0.00005,              # -0.005% (40th percentile)
        "neutral_high": 0.00005,              # +0.005% (60th percentile)
        "max_hold_hours": 24,
        "stop_loss_pct": 0.02,                # 2%
        "position_size_usd": 10_000,
    }

    def generate_signals(self, df: pd.DataFrame, t: int) -> Optional[str]:
        """
        Returns: "long" | "short" | None
        Uses only df.iloc[:t+1] (no look-ahead)
        """
        if df is None or df.empty or t < 60:
            return None

        if "funding_rate" not in df.columns:
            return None

        current = df.iloc[t]
        funding_rate = current.get("funding_rate")
        if pd.isna(funding_rate):
            return None

        # Entry rules
        if funding_rate < self.params["funding_long_threshold"]:
            return "long"
        elif funding_rate > self.params["funding_short_threshold"]:
            return "short"

        return None

    def check_exit(self, position: Position, df: pd.DataFrame, t: int) -> Tuple[bool, str]:
        """
        Returns: (should_exit, exit_reason)
        exit_reason: "mean_reversion" | "time_based" | "stop_loss"
        """
        if position.side == "flat":
            return False, ""

        current = df.iloc[t]
        current_price = current.get("close", position.entry_price)
        current_time_ms = int(df.index[t])

        # Time-based exit
        hold_time_min = (current_time_ms - position.entry_time_ms) / 60000.0
        if hold_time_min >= self.params["max_hold_hours"] * 60:
            return True, "time_based"

        # Stop-loss: 2% from entry price
        if position.side == "long":
            sl_price = position.entry_price * (1 - self.params["stop_loss_pct"])
            if current_price <= sl_price:
                return True, "stop_loss"
        elif position.side == "short":
            sl_price = position.entry_price * (1 + self.params["stop_loss_pct"])
            if current_price >= sl_price:
                return True, "stop_loss"

        # Mean reversion exit: funding returns to neutral zone
        if "funding_rate" in df.columns:
            funding_rate = current.get("funding_rate")
            if not pd.isna(funding_rate):
                neutral_low = self.params["neutral_low"]
                neutral_high = self.params["neutral_high"]
                if neutral_low <= funding_rate <= neutral_high:
                    return True, "mean_reversion"

        return False, ""
