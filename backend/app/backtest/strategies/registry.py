"""Base strategy class and strategy registry.

Separated into its own module to avoid circular imports
between strategy implementations and the registry.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from app.backtest.config import Position


class BaseStrategy(ABC):
    """Abstract base class for all backtest strategies."""

    DEFAULT_PARAMS: Dict[str, Any] = {}

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize strategy with optional parameter overrides."""
        self.params = {**self.DEFAULT_PARAMS, **(params or {})}

    def get_params(self) -> Dict[str, Any]:
        return self.params

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, t: int) -> Optional[str]:
        """
        Returns: "long" | "short" | None
        df: full DataFrame (strategy must only use df.iloc[:t+1])
        t: current bar index
        """
        ...

    @abstractmethod
    def check_exit(self, position: Position, df: pd.DataFrame, t: int) -> Tuple[bool, str]:
        """
        Returns: (should_exit, exit_reason)
        exit_reason: "mean_reversion" | "time_based" | "stop_loss" | "take_profit" | "basis_compression"
        """
        ...


# Registry populated by individual strategy modules
STRATEGY_REGISTRY: Dict[str, type] = {}


def register_strategy(name: str):
    """Decorator to register a strategy class."""
    def decorator(cls: type):
        STRATEGY_REGISTRY[name] = cls
        return cls
    return decorator
