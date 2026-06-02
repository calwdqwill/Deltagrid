"""S04: Liquidation Cascade Fade strategy.

Идея: liquidation cascades создают экстремальное движение цены.
После cascade цена часто отскакивает (fade).
Торгуем против направления cascade.

Entry rules:
  - Long:  liq_spike_1h > 95th percentile AND price_change_1h < -3%
  - Short: liq_spike_1h > 95th percentile AND price_change_1h > +3%

Exit rules:
  - Time-based: hold_hours (default 6)
  - Price recovery: 50% of initial move
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from app.backtest.config import Position
from app.backtest.strategies.registry import BaseStrategy, register_strategy


@register_strategy("liquidation_cascade_fade")
class LiquidationCascadeFadeStrategy(BaseStrategy):
    """S04: Liquidation Cascade Fade."""

    DEFAULT_PARAMS = {
        "liq_percentile_threshold": 95.0,   # 95th percentile
        "price_move_threshold": 0.015,       # 1.5% move in 1 hour (adjusted for dataset volatility)
        "hold_hours": 6,
        "recovery_pct": 0.5,                 # exit at 50% recovery
        "position_size_usd": 10_000,
    }

    def generate_signals(self, df: pd.DataFrame, t: int) -> Optional[str]:
        """
        Returns: "long" | "short" | None
        Uses only df.iloc[:t+1] (no look-ahead)
        """
        if df is None or df.empty or t < 1440:
            return None

        # Detect liquidation spike
        liq_spike, _ = self.detect_liquidation_spike(df, t)
        if not liq_spike:
            return None

        # Detect price move
        move_triggered, direction, _ = self.detect_price_move(df, t)
        if not move_triggered:
            return None

        # Trade against the cascade
        if direction == "down":
            return "long"
        elif direction == "up":
            return "short"

        return None

    def check_exit(self, position: Position, df: pd.DataFrame, t: int) -> Tuple[bool, str]:
        """
        Returns: (should_exit, exit_reason)
        exit_reason: "time_based" | "recovery"
        """
        if position.side == "flat":
            return False, ""

        current = df.iloc[t]
        current_price = current.get("close", position.entry_price)
        current_time_ms = int(df.index[t])

        # Time-based exit
        hold_time_min = (current_time_ms - position.entry_time_ms) / 60000.0
        if hold_time_min >= self.params["hold_hours"] * 60:
            return True, "time_based"

        # Recovery exit: 50% of initial move recovered
        entry_price = position.entry_price
        if entry_price == 0:
            return False, ""

        if position.side == "long":
            # We entered long after a drop. Exit when price recovers.
            recovery_target = entry_price * (1 + self.params["recovery_pct"] * self.params["price_move_threshold"])
            if current_price >= recovery_target:
                return True, "recovery"
        elif position.side == "short":
            recovery_target = entry_price * (1 - self.params["recovery_pct"] * self.params["price_move_threshold"])
            if current_price <= recovery_target:
                return True, "recovery"

        return False, ""

    def detect_liquidation_spike(self, df: pd.DataFrame, t: int) -> Tuple[bool, float]:
        """
        Checks if last 1h liquidation volume is above 95th percentile
        of historical distribution.
        Uses only df.iloc[:t+1] to calculate percentile (no look-ahead).
        """
        if "liq_sum_1h" not in df.columns:
            return False, 0.0

        liq_sum_1h = float(df["liq_sum_1h"].iloc[t])
        if pd.isna(liq_sum_1h):
            return False, 0.0

        # Historical percentile using all previous hourly sums
        # Exclude current hour and use every 60th prior sum to avoid overlap bias
        if t < 120:
            return False, 0.0

        historical = df["liq_sum_1h"].iloc[: t - 59]
        if historical.empty or historical.isna().all():
            return False, 0.0

        # Sample every 60th value to get non-overlapping hourly sums
        sampled = historical.iloc[::60].dropna().values
        if len(sampled) < 10:
            return False, 0.0

        percentile = self.params["liq_percentile_threshold"]
        threshold = np.percentile(sampled, percentile)

        return liq_sum_1h > threshold, liq_sum_1h

    def detect_price_move(self, df: pd.DataFrame, t: int) -> Tuple[bool, str, float]:
        """
        Checks if price moved > threshold in last 1 hour.
        Returns: (triggered, direction "up"/"down", move_pct)
        """
        if "price_change_1h" not in df.columns:
            return False, "", 0.0

        move_pct = float(df["price_change_1h"].iloc[t])
        if pd.isna(move_pct):
            return False, "", 0.0

        threshold = self.params["price_move_threshold"]

        if move_pct > threshold:
            return True, "up", move_pct
        elif move_pct < -threshold:
            return True, "down", move_pct

        return False, "", move_pct
