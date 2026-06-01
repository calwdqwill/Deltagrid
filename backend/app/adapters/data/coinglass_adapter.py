"""CoinGlassDataAdapter — market data ingestion for CoinGlass API V4.

Docs: https://docs.coinglass.com/reference
Base URL: https://open-api-v4.coinglass.com
Auth: header "CG-API-KEY": "YOUR_KEY"

Endpoints:
- /api/futures/funding-rate/history                  — funding rate OHLC
- /api/futures/open-interest/history                 — open interest OHLC
- /api/futures/liquidation/history                   — liquidation history
- /api/futures/global-long-short-account-ratio/history — L/S ratio history
"""

import logging
from typing import Optional

import httpx

from app.config import get_settings

from .base_adapter import BaseDataAdapter
from .data_models import (
    FundingRate,
    Liquidation,
    LongShortRatio,
    OHLCVCandle,
    OpenInterest,
    ProviderHealthStatus,
)
from .data_writer import DataWriter
from .rate_limiter import GlobalRateLimiter, RetryPolicy
from .symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)

COINGLASS_V4_BASE = "https://open-api-v4.coinglass.com"


class CoinGlassDataAdapter(BaseDataAdapter):
    """CoinGlass V4 API data adapter for perp metrics."""

    source_name = "coinglass"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
        symbol_mapper: Optional[SymbolMapper] = None,
        data_writer: Optional[DataWriter] = None,
    ):
        super().__init__(rate_limiter, retry_policy)
        settings = get_settings()
        self.api_key = settings.coinglass_api_key
        self.base_url = getattr(settings, "coinglass_standard_base_url", COINGLASS_V4_BASE).rstrip("/")
        self.symbol_mapper = symbol_mapper or SymbolMapper()
        self.writer = data_writer or DataWriter()

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["CG-API-KEY"] = self.api_key
        return headers

    def _native_symbol(self, canonical: str, exchange: str) -> str:
        """Resolve canonical symbol to provider-native pair symbol."""
        try:
            return self.symbol_mapper.to_provider(canonical, exchange, alias_type="ticker")
        except ValueError:
            if exchange == "okx":
                return f"{canonical}-USDT-SWAP"
            if exchange == "hyperliquid":
                return canonical
            return f"{canonical}USDT"

    @staticmethod
    def _exchange_funding_interval(exchange: str) -> int:
        """Return funding interval in hours per exchange."""
        return 1 if exchange.lower() == "hyperliquid" else 8

    # -- Funding rates -------------------------------------------------

    async def fetch_funding(
        self,
        symbol: str,
        start_ms: int,
        end_ms: int,
    ) -> list[FundingRate]:
        """Fetch funding rate history for a symbol."""
        results = []
        instrument = self.symbol_mapper.resolve_instrument(symbol)
        if not instrument:
            logger.warning(f"[CoinGlass] No instrument found for {symbol}")
            return results

        exchange = instrument.exchange
        native = self._native_symbol(symbol, exchange)
        interval_hours = self._exchange_funding_interval(exchange)

        url = f"{self.base_url}/api/futures/funding-rate/history"
        params = {
            "exchange": exchange.capitalize(),
            "symbol": native,
            "interval": "1h",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        try:
            data = await self._execute_with_protection(_do_request)
            for row in data.get("data", []):
                results.append(
                    FundingRate(
                        timestamp_ms=int(row["time"]),
                        symbol=symbol,
                        exchange=exchange,
                        funding_rate=float(row["close"]),
                        next_funding_time_ms=None,
                        interval=f"{interval_hours}h",
                    )
                )
        except Exception as e:
            logger.warning(f"[CoinGlass] fetch_funding failed for {symbol}: {e}")

        return results

    # -- Open interest -------------------------------------------------

    async def fetch_oi(
        self,
        symbol: str,
        interval: str = "1h",
    ) -> list[OpenInterest]:
        results = []
        instrument = self.symbol_mapper.resolve_instrument(symbol)
        if not instrument:
            return results

        exchange = instrument.exchange
        native = self._native_symbol(symbol, exchange)

        url = f"{self.base_url}/api/futures/open-interest/history"
        params = {
            "exchange": exchange.capitalize(),
            "symbol": native,
            "interval": interval,
            "limit": 1000,
            "unit": "usd",
        }

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        try:
            data = await self._execute_with_protection(_do_request)
            for row in data.get("data", []):
                results.append(
                    OpenInterest(
                        timestamp_ms=int(row["time"]),
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        oi_usd=float(row["close"]),
                        oi_coins=None,
                    )
                )
        except Exception as e:
            logger.warning(f"[CoinGlass] fetch_oi failed for {symbol}: {e}")

        return results

    # -- Liquidations --------------------------------------------------

    async def fetch_liquidations(
        self,
        symbol: str,
        start_ms: int,
        end_ms: int,
    ) -> list[Liquidation]:
        results = []
        instrument = self.symbol_mapper.resolve_instrument(symbol)
        if not instrument:
            return results

        exchange = instrument.exchange
        native = self._native_symbol(symbol, exchange)

        url = f"{self.base_url}/api/futures/liquidation/history"
        params = {
            "exchange": exchange.capitalize(),
            "symbol": native,
            "interval": "1h",
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        try:
            data = await self._execute_with_protection(_do_request)
            for row in data.get("data", []):
                # V4 returns aggregated long+short per interval; we split into 2 records
                ts = int(row["time"])
                long_usd = float(row.get("long_liquidation_usd", 0))
                short_usd = float(row.get("short_liquidation_usd", 0))
                if long_usd > 0:
                    results.append(
                        Liquidation(
                            timestamp_ms=ts,
                            symbol=symbol,
                            exchange=exchange,
                            side="long",
                            quantity=0.0,
                            price=0.0,
                            value_usd=long_usd,
                        )
                    )
                if short_usd > 0:
                    results.append(
                        Liquidation(
                            timestamp_ms=ts,
                            symbol=symbol,
                            exchange=exchange,
                            side="short",
                            quantity=0.0,
                            price=0.0,
                            value_usd=short_usd,
                        )
                    )
        except Exception as e:
            logger.warning(f"[CoinGlass] fetch_liquidations failed for {symbol}: {e}")

        return results

    # -- Long/Short ratio ----------------------------------------------

    async def fetch_long_short_ratio(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
    ) -> list[LongShortRatio]:
        results = []
        instrument = self.symbol_mapper.resolve_instrument(symbol)
        if not instrument:
            return results

        exchange = instrument.exchange
        native = self._native_symbol(symbol, exchange)

        url = f"{self.base_url}/api/futures/global-long-short-account-ratio/history"
        params = {
            "exchange": exchange.capitalize(),
            "symbol": native,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": 1000,
        }

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        try:
            data = await self._execute_with_protection(_do_request)
            for row in data.get("data", []):
                results.append(
                    LongShortRatio(
                        timestamp_ms=int(row["time"]),
                        symbol=symbol,
                        exchange=exchange,
                        interval=interval,
                        long_ratio=float(row.get("global_account_long_percent", 0)),
                        short_ratio=float(row.get("global_account_short_percent", 0)),
                        long_account_ratio=float(row.get("global_account_long_percent")) if "global_account_long_percent" in row else None,
                        short_account_ratio=float(row.get("global_account_short_percent")) if "global_account_short_percent" in row else None,
                    )
                )
        except Exception as e:
            logger.warning(f"[CoinGlass] fetch_long_short_ratio failed for {symbol}: {e}")

        return results

    # -- OHLCV (not supported by CoinGlass) ----------------------------

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1000,
    ) -> list[OHLCVCandle]:
        """CoinGlass does not provide OHLCV."""
        return []

    # -- Health check --------------------------------------------------

    async def health_check(self) -> ProviderHealthStatus:
        if not self.api_key:
            return ProviderHealthStatus(
                source_name=self.source_name,
                is_healthy=False,
                last_error="API key not configured",
                circuit_breaker_state=self.circuit_breaker.state.value,
            )
        url = f"{self.base_url}/api/futures/funding-rate/history"
        try:
            import time as _time
            t0 = _time.monotonic()
            resp = await self.client.get(
                url,
                headers=self._headers(),
                params={
                    "exchange": "Binance",
                    "symbol": "BTCUSDT",
                    "interval": "1h",
                    "limit": 1,
                },
            )
            latency = int((_time.monotonic() - t0) * 1000)
            healthy = resp.status_code == 200
            if healthy:
                data = resp.json()
                healthy = data.get("code") == "0"
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
