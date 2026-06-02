"""S02: Spot/Perp Basis Compression strategy.

Идея: perpetual futures торгуются с premium/discount к споту (basis).
Basis = (perp_price - spot_price) / spot_price
Когда basis экстремально широкий — открываем позицию против basis.

MVP упрощение: у нас нет реального спот потока.
Используем proxy: basis = (close - sma_24h) / sma_24h
FIXME: replace with real spot price when spot adapter added
"""

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from app.backtest.config import Position
from app.backtest.strategies.registry import BaseStrategy, register_strategy


@register_strategy("basis_compression")
class BasisCompressionStrategy(BaseStrategy):
    """S02: Spot/Perp Basis Compression (simplified MVP version)."""

    DEFAULT_PARAMS = {
        "basis_long_threshold": -0.001,    # -0.1%
        "basis_short_threshold": 0.002,     # +0.2%
        "max_hold_hours": 48,
        "position_size_usd": 10_000,
        "cooldown_min": 60,                # minimum minutes between trades
    }

    def __init__(self, params=None):
        super().__init__(params)
        self._last_exit_time_ms = 0

    def generate_signals(self, df: pd.DataFrame, t: int) -> Optional[str]:
        """
        Returns: "long" | "short" | None
        Uses only df.iloc[:t+1] (no look-ahead)
        """
        if df is None or df.empty or t < 1440:
            return None

        current_time_ms = int(df.index[t])
        cooldown_ms = self.params["cooldown_min"] * 60000
        if current_time_ms - self._last_exit_time_ms < cooldown_ms:
            return None

        # Calculate proxy basis = (close - sma_24h) / sma_24h
        # Only use data up to t
        closes = df["close"].iloc[: t + 1]
        sma_24h = closes.iloc[-1440:].mean()
        current_close = closes.iloc[-1]

        if pd.isna(sma_24h) or sma_24h == 0:
            return None

        basis = (current_close - sma_24h) / sma_24h

        # Entry rules
        if basis < self.params["basis_long_threshold"]:
            return "long"
        elif basis > self.params["basis_short_threshold"]:
            return "short"

        return None

    def check_exit(self, position: Position, df: pd.DataFrame, t: int) -> Tuple[bool, str]:
        """
        Returns: (should_exit, exit_reason)
        exit_reason: "basis_compression" | "time_based"
        """
        if position.side == "flat":
            return False, ""

        current_time_ms = int(df.index[t])

        # Time-based exit
        hold_time_min = (current_time_ms - position.entry_time_ms) / 60000.0
        if hold_time_min >= self.params["max_hold_hours"] * 60:
            self._last_exit_time_ms = current_time_ms
            return True, "time_based"

        # Basis returns to 0 (crosses zero line)
        closes = df["close"].iloc[: t + 1]
        sma_24h = closes.iloc[-1440:].mean()
        current_close = closes.iloc[-1]

        if pd.isna(sma_24h) or sma_24h == 0:
            return False, ""

        basis = (current_close - sma_24h) / sma_24h

        # Exit when basis crosses zero (compression complete)
        if position.side == "long" and basis >= 0:
            self._last_exit_time_ms = current_time_ms
            return True, "basis_compression"
        elif position.side == "short" and basis <= 0:
            self._last_exit_time_ms = current_time_ms
            return True, "basis_compression"

        return False, ""
