"""BinanceAdapter — market data ingestion for Binance futures.

Fetches 1m (and other intervals) OHLCV from Binance USD-M Futures API.
Implements gap detection and data-quality logging.
"""

import logging
from typing import Optional

from .base_adapter import BaseDataAdapter
from .data_models import OHLCVCandle, ProviderHealthStatus
from .data_writer import DataWriter
from .rate_limiter import GlobalRateLimiter, RetryPolicy
from .symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)

BINANCE_FAPI_BASE = "https://fapi.binance.com"


class BinanceAdapter(BaseDataAdapter):
    """Binance USD-M Futures data adapter."""

    source_name = "binance"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
        symbol_mapper: Optional[SymbolMapper] = None,
        data_writer: Optional[DataWriter] = None,
    ):
        super().__init__(rate_limiter, retry_policy)
        self.symbol_mapper = symbol_mapper or SymbolMapper()
        self.writer = data_writer or DataWriter()

    def _native_symbol(self, canonical: str) -> str:
        """Canonical symbol -> Binance-native symbol (e.g. BTC -> BTCUSDT)."""
        try:
            return self.symbol_mapper.to_provider(canonical, "binance", alias_type="ticker")
        except ValueError:
            return f"{canonical}USDT"

    # ------------------------------------------------------------------
    # OHLCV
    # ------------------------------------------------------------------

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1500,
    ) -> list[OHLCVCandle]:
        """Fetch OHLCV candles (single request)."""
        native_symbol = self._native_symbol(symbol)
        url = f"{BINANCE_FAPI_BASE}/fapi/v1/klines"
        params = {
            "symbol": native_symbol,
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
        candles: list[OHLCVCandle] = []
        interval_ms = self._interval_to_ms(interval)

        for i, raw in enumerate(data):
            candle = self._normalize_candle(raw, symbol, interval)
            candles.append(candle)

            # Gap detection within chunk
            if i > 0:
                prev_ts = candles[i - 1].timestamp_ms
                gap = candle.timestamp_ms - prev_ts
                if gap > 2 * interval_ms:
                    logger.warning(
                        f"[Binance] Gap >2 intervals for {symbol}: "
                        f"{gap // interval_ms} intervals between {prev_ts} and {candle.timestamp_ms}"
                    )
                    self.writer.log_data_quality(
                        table_name="ohlcv",
                        check_type="gap",
                        severity="warning",
                        symbol=symbol,
                        exchange="binance",
                        interval=interval,
                        gap_start=prev_ts,
                        gap_end=candle.timestamp_ms,
                        details_json=f'{{"gap_ms": {gap}, "interval_ms": {interval_ms}}}',
                    )

        return candles

    # ------------------------------------------------------------------
    # Stubs for other data types
    # ------------------------------------------------------------------

    async def fetch_funding(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """Stub — funding rates for Binance."""
        return []

    async def fetch_oi(self, symbol: str, interval: str = "1h") -> list:
        """Stub — open interest for Binance."""
        return []

    async def fetch_liquidations(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """Stub — liquidations for Binance."""
        return []

    async def fetch_long_short_ratio(
        self, symbol: str, interval: str, start_ms: int, end_ms: int
    ) -> list:
        """Stub — long/short ratio for Binance."""
        return []

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health_check(self) -> ProviderHealthStatus:
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
    def _normalize_candle(raw: list, canonical_symbol: str, interval: str) -> OHLCVCandle:
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
            quote_volume=float(raw[7]) if len(raw) > 7 else None,
            trades_count=int(raw[8]) if len(raw) > 8 else None,
            symbol=canonical_symbol,
            exchange="binance",
            interval=interval,
        )

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
