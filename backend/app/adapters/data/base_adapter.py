"""BaseDataAdapter — abstract base for market data ingestion adapters.

NOTE: Named BaseDataAdapter to avoid conflict with BaseAdapter (scanner) in app.adapters.base.
"""

from abc import ABC, abstractmethod
from typing import Optional

import httpx

from .data_models import (
    FundingRate,
    Liquidation,
    LongShortRatio,
    OHLCVCandle,
    OpenInterest,
    ProviderHealthStatus,
)
from .rate_limiter import CircuitBreaker, GlobalRateLimiter, RetryPolicy


class BaseDataAdapter(ABC):
    """Abstract base for all market data ingestion adapters.

    Responsibilities:
    1. Speak native exchange API.
    2. Normalize responses into CanonicalDataFormat (Pydantic models).
    3. Respect rate limits via GlobalRateLimiter.
    4. Report health via CircuitBreaker.
    5. Map canonical symbols to provider-native symbols via SymbolMapper.
    """

    source_name: str = "unknown"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        self.rate_limiter = rate_limiter
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = CircuitBreaker()
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self.client.aclose()

    # ------------------------------------------------------------------
    # Abstract methods — must be implemented by each exchange
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1000,
    ) -> list[OHLCVCandle]:
        """Fetch OHLCV candles for a symbol.

        Args:
            symbol: Provider-native symbol (e.g. "BTCUSDT" for Binance).
            interval: Candle interval — "1m", "5m", "1h", "1d".
            start_ms: Start timestamp in milliseconds (inclusive).
            end_ms: End timestamp in milliseconds (inclusive).
            limit: Maximum candles per request.
        """
        ...

    @abstractmethod
    async def fetch_funding(
        self,
        symbol: str,
        start_ms: int,
        end_ms: int,
    ) -> list[FundingRate]:
        """Fetch funding rate history."""
        ...

    @abstractmethod
    async def fetch_oi(
        self,
        symbol: str,
        interval: str = "1h",
    ) -> list[OpenInterest]:
        """Fetch open interest history."""
        ...

    @abstractmethod
    async def fetch_liquidations(
        self,
        symbol: str,
        start_ms: int,
        end_ms: int,
    ) -> list[Liquidation]:
        """Fetch liquidation history."""
        ...

    @abstractmethod
    async def fetch_long_short_ratio(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
    ) -> list[LongShortRatio]:
        """Fetch long/short ratio history."""
        ...

    @abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Quick connectivity check. Returns health status."""
        ...

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _execute_with_protection(self, coro_fn, *args, **kwargs):
        """Wrap a call with rate limit + circuit breaker + retry."""
        await self.rate_limiter.acquire(self.source_name)
        return await self.circuit_breaker.call(
            lambda: self.retry_policy.execute(coro_fn, *args, **kwargs)
        )


class DataAdapterRegistry:
    """Runtime registry for data adapters."""

    def __init__(self):
        self._adapters: dict[str, BaseDataAdapter] = {}

    def register(self, name: str, adapter: BaseDataAdapter) -> None:
        self._adapters[name] = adapter

    def get(self, name: str) -> Optional[BaseDataAdapter]:
        return self._adapters.get(name)

    def list_adapters(self) -> list[str]:
        return list(self._adapters.keys())

    async def health_check_all(self) -> dict[str, ProviderHealthStatus]:
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = await adapter.health_check()
            except Exception as e:
                results[name] = ProviderHealthStatus(
                    source_name=name,
                    is_healthy=False,
                    last_error=str(e),
                )
        return results


class FallbackChain:
    """Chain of adapters for fallback fetching.

    If primary adapter is unavailable (CB OPEN), try next in chain.
    """

    def __init__(self, adapters: list[BaseDataAdapter]):
        self.adapters = adapters

    async def fetch_ohlcv(self, *args, **kwargs) -> list[OHLCVCandle]:
        for adapter in self.adapters:
            if adapter.circuit_breaker.can_execute():
                try:
                    return await adapter.fetch_ohlcv(*args, **kwargs)
                except Exception:
                    continue
        return []

    async def fetch_funding(self, *args, **kwargs) -> list[FundingRate]:
        for adapter in self.adapters:
            if adapter.circuit_breaker.can_execute():
                try:
                    return await adapter.fetch_funding(*args, **kwargs)
                except Exception:
                    continue
        return []
