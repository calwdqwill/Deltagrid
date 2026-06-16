"""Rate limiting, retry, and circuit breaker for data adapters.

Components:
- TokenBucket: per-provider rate limiting
- RetryPolicy: exponential backoff with jitter
- CircuitBreaker: fail-fast for degraded providers
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when the circuit breaker is OPEN."""
    pass


class RateLimitExceeded(Exception):
    """Raised when rate limit is hit."""
    pass


class AdapterError(Exception):
    """Base exception for adapter failures."""
    pass


@dataclass
class TokenBucket:
    """Async token bucket rate limiter.

    Args:
        capacity: Maximum tokens in the bucket.
        refill_rate: Tokens added per second.
    """

    capacity: float
    refill_rate: float
    _tokens: float = field(default=None, repr=False)
    _last_refill: float = field(default_factory=time.monotonic, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def acquire(self, cost: float = 1.0) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill

            if self._tokens is None:
                self._tokens = self.capacity
            else:
                self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)

            self._last_refill = now

            if self._tokens < cost:
                wait = (cost - self._tokens) / self.refill_rate
                logger.debug(f"TokenBucket: waiting {wait:.2f}s for {cost} tokens")
                await asyncio.sleep(wait)
                self._tokens = self.capacity - cost
            else:
                self._tokens -= cost


@dataclass
class RetryPolicy:
    """Exponential backoff retry policy.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        jitter: Maximum random jitter in seconds.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = 1.0

    async def execute(self, coro_fn, *args, **kwargs):
        """Execute coroutine with retry logic."""
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return await coro_fn(*args, **kwargs)
            except (AdapterError, RateLimitExceeded, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                    delay += random.uniform(0, self.jitter)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.max_retries} after {delay:.2f}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise last_exception
        raise last_exception


@dataclass
class CircuitBreaker:
    """Circuit breaker for preventing cascade failures.

    States:
    - CLOSED: requests pass through, failures counted.
    - OPEN: all requests rejected immediately.
    - HALF_OPEN: one probe request allowed.
    """

    failure_threshold: int = 5
    cooldown_seconds: float = 60.0
    half_open_probe: int = 1

    _state: CircuitBreakerState = field(default=CircuitBreakerState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)
    _half_open_attempts: int = field(default=0, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    def can_execute(self) -> bool:
        """Check if a request is allowed to proceed."""
        if self._state == CircuitBreakerState.CLOSED:
            return True
        if self._state == CircuitBreakerState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.cooldown_seconds:
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_attempts = 0
                logger.info("CircuitBreaker: OPEN -> HALF_OPEN")
                return True
            return False
        # HALF_OPEN
        if self._half_open_attempts < self.half_open_probe:
            return True
        return False

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.CLOSED
                self._failure_count = 0
                self._half_open_attempts = 0
                logger.info("CircuitBreaker: HALF_OPEN -> CLOSED")
            else:
                self._failure_count = max(0, self._failure_count - 1)

    async def record_failure(self) -> None:
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.OPEN
                self._half_open_attempts = 0
                logger.warning("CircuitBreaker: HALF_OPEN -> OPEN")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                logger.warning(f"CircuitBreaker: CLOSED -> OPEN ({self._failure_count} failures)")

    async def call(self, coro_fn, *args, **kwargs):
        """Execute coroutine through the circuit breaker."""
        if not self.can_execute():
            raise CircuitBreakerOpen(f"Circuit breaker is {self._state.value}")

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._half_open_attempts += 1

        try:
            result = await coro_fn(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise


class GlobalRateLimiter:
    """Shared rate limiter across all data adapters.

    Prevents one aggressive job from starving others.
    """

    DEFAULT_LIMITS = {
        "binance": (20.0, 20.0),      # 20 req/sec
        "bybit": (120.0, 120.0),      # 120 req/sec
        "okx": (5.0, 2.0),            # conservative public API pacing
        "hyperliquid": (100.0, 100.0), # 100 req/sec
        "coinglass": (3.0, 3.0),      # 3 req/sec
        "coingecko": (8.0, 8.0),      # 500/min = ~8/sec
    }

    def __init__(self, limits: dict[str, tuple[float, float]] | None = None):
        self.buckets: dict[str, TokenBucket] = {}
        limits = limits or self.DEFAULT_LIMITS
        for name, (capacity, rate) in limits.items():
            self.buckets[name] = TokenBucket(capacity=capacity, refill_rate=rate)
        self._global_sem = asyncio.Semaphore(50)  # max 50 concurrent requests

    async def acquire(self, adapter_name: str, cost: float = 1.0) -> None:
        async with self._global_sem:
            bucket = self.buckets.get(adapter_name)
            if bucket:
                await bucket.acquire(cost)
