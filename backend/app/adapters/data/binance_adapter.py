"""BinanceAdapter — market data ingestion for Binance futures.

Implements fetch_ohlcv_1m with rate limiting, retry, and circuit breaker.
Uses mock data for prototype testing (no real API calls in demo mode).
"""

import logging
from typing import Optional

import httpx

from .base_adapter import BaseDataAdapter
from .data_models import OHLCVCandle, ProviderHealthStatus
from .rate_limiter import GlobalRateLimiter, RetryPolicy

logger = logging.getLogger(__name__)

BINANCE_FAPI_BASE = "https://fapi.binance.com"


class BinanceAdapter(BaseDataAdapter):
    """Binance USD-M Futures data adapter."""

    source_name = "binance"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
        use_mock: bool = False,
    ):
        super().__init__(rate_limiter, retry_policy)
        self.use_mock = use_mock

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1500,
    ) -> list[OHLCVCandle]:
        """Fetch OHLCV from Binance futures API.

        Args:
            symbol: Binance-native symbol, e.g. "BTCUSDT".
            interval: "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d".
        """
        if self.use_mock:
            return self._mock_ohlcv(symbol, interval, start_ms, end_ms, limit)

        url = f"{BINANCE_FAPI_BASE}/fapi/v1/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": limit,
        }

        async def _do_request():
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

        data = await self._execute_with_protection(_do_request)
        return [self._normalize_candle(raw, symbol, interval) for raw in data]

    async def fetch_funding(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """Stub — funding rates for Binance."""
        # TODO: implement /fapi/v1/fundingRate
        return []

    async def fetch_oi(self, symbol: str, interval: str = "1h") -> list:
        """Stub — open interest for Binance."""
        # TODO: implement /fapi/v1/openInterestHist
        return []

    async def fetch_liquidations(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """Stub — liquidations for Binance."""
        # TODO: implement /fapi/v1/allForceOrders or /fapi/v1/forceOrders
        return []

    async def fetch_long_short_ratio(
        self, symbol: str, interval: str, start_ms: int, end_ms: int
    ) -> list:
        """Stub — long/short ratio for Binance."""
        # TODO: implement /futures/data/globalLongShortAccountRatio
        return []

    async def health_check(self) -> ProviderHealthStatus:
        if self.use_mock:
            return ProviderHealthStatus(
                source_name=self.source_name,
                is_healthy=True,
                latency_ms=50,
                circuit_breaker_state=self.circuit_breaker.state.value,
            )

        url = f"{BINANCE_FAPI_BASE}/fapi/v1/ping"
        try:
            import time as _time

            t0 = _time.monotonic()
            resp = await self.client.get(url)
            latency = int((_time.monotonic() - t0) * 1000)
            healthy = resp.status_code == 200
        except Exception as e:
            return ProviderHealthStatus(
                source_name=self.source_name,
                is_healthy=False,
                last_error=str(e),
                circuit_breaker_state=self.circuit_breaker.state.value,
            )

        return ProviderHealthStatus(
            source_name=self.source_name,
            is_healthy=healthy,
            latency_ms=latency,
            circuit_breaker_state=self.circuit_breaker.state.value,
        )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_candle(raw: list, symbol: str, interval: str) -> OHLCVCandle:
        """Normalize Binance kline array into OHLCVCandle.

        Binance kline format:
        [
            1499040000000,      // Open time
            "0.01634790",       // Open
            "0.80000000",       // High
            "0.01575800",       // Low
            "0.01577100",       // Close
            "148976.11427815",  // Volume
            1499644799999,      // Close time
            "2434.19055334",    // Quote asset volume
            308,                // Number of trades
            ...
        ]
        """
        return OHLCVCandle(
            timestamp_ms=int(raw[0]),
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=float(raw[5]),
            quote_volume=float(raw[7]),
            trades_count=int(raw[8]),
            symbol=symbol,
            exchange="binance",
            interval=interval,
        )

    # ------------------------------------------------------------------
    # Mock data for prototype testing
    # ------------------------------------------------------------------

    def _mock_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int,
    ) -> list[OHLCVCandle]:
        """Generate deterministic mock OHLCV candles."""
        import random as _random

        _random.seed(symbol + str(start_ms))
        candles = []
        interval_ms = self._interval_to_ms(interval)
        current = start_ms
        price = 50000.0 if "BTC" in symbol else 3000.0

        count = 0
        while current < end_ms and count < limit:
            change = _random.uniform(-0.002, 0.002)
            open_p = price
            close_p = price * (1 + change)
            high_p = max(open_p, close_p) * (1 + _random.uniform(0, 0.001))
            low_p = min(open_p, close_p) * (1 - _random.uniform(0, 0.001))
            volume = _random.uniform(10.0, 1000.0)

            candles.append(
                OHLCVCandle(
                    timestamp_ms=current,
                    open=round(open_p, 2),
                    high=round(high_p, 2),
                    low=round(low_p, 2),
                    close=round(close_p, 2),
                    volume=round(volume, 4),
                    quote_volume=round(volume * close_p, 2),
                    trades_count=int(_random.uniform(100, 5000)),
                    symbol=symbol,
                    exchange="binance",
                    interval=interval,
                )
            )
            price = close_p
            current += interval_ms
            count += 1

        logger.info(f"[MOCK] Generated {len(candles)} candles for {symbol} {interval}")
        return candles

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        mapping = {
            "1m": 60_000,
            "3m": 180_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "2h": 7_200_000,
            "4h": 14_400_000,
            "6h": 21_600_000,
            "8h": 28_800_000,
            "12h": 43_200_000,
            "1d": 86_400_000,
        }
        return mapping.get(interval, 60_000)
