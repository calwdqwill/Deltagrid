"""Strategy package — imports registry and loads all strategies."""

from app.backtest.strategies.registry import BaseStrategy, STRATEGY_REGISTRY, register_strategy

# Load all strategies to populate STRATEGY_REGISTRY
from app.backtest.strategies.funding_mean_reversion import FundingMeanReversionStrategy  # noqa: F401, E402
from app.backtest.strategies.basis_compression import BasisCompressionStrategy  # noqa: F401, E402
from app.backtest.strategies.liquidation_cascade_fade import LiquidationCascadeFadeStrategy  # noqa: F401, E402
