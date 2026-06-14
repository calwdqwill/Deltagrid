"""DeltaGrid Data Layer — market data ingestion adapters.

Backtesting-first research terminal data pipeline:
- OHLCV, funding rates, open interest, liquidations, long/short ratios
- Provider adapters with rate limiting, circuit breaker, retry
- Symbol mapping across exchanges
- PostgreSQL persistence via Alembic migrations
"""

from .base_adapter import BaseDataAdapter, DataAdapterRegistry, FallbackChain
from .binance_adapter import BinanceAdapter
from .data_models import (
    BackfillResult,
    FundingRate,
    Liquidation,
    LongShortRatio,
    OHLCVCandle,
    OpenInterest,
    ProviderHealthStatus,
)
from .okx_adapter import OkxAdapter
from .rate_limiter import CircuitBreaker, GlobalRateLimiter, RetryPolicy, TokenBucket
from .symbol_mapper import Instrument, InstrumentAlias, SymbolMapper

__all__ = [
    "BaseDataAdapter",
    "DataAdapterRegistry",
    "FallbackChain",
    "BinanceAdapter",
    "OkxAdapter",
    "BackfillResult",
    "FundingRate",
    "Liquidation",
    "LongShortRatio",
    "OHLCVCandle",
    "OpenInterest",
    "ProviderHealthStatus",
    "CircuitBreaker",
    "GlobalRateLimiter",
    "RetryPolicy",
    "TokenBucket",
    "Instrument",
    "InstrumentAlias",
    "SymbolMapper",
]
