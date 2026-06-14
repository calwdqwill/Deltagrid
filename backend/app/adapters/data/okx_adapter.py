"""OKXAdapter - market data ingestion for OKX USDT perpetual swaps."""

import logging
from typing import Any, Optional

import httpx

from .base_adapter import BaseDataAdapter
from .data_models import (
    FundingRate,
    Liquidation,
    LongShortRatio,
    OHLCVCandle,
    OpenInterest,
    ProviderHealthStatus,
)
from .rate_limiter import AdapterError, GlobalRateLimiter, RetryPolicy
from .symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)

OKX_PUBLIC_BASE = "https://www.okx.com"
OKX_MAX_CANDLES = 300


class OkxAdapter(BaseDataAdapter):
    """OKX public market data adapter for USDT swap instruments."""

    source_name = "okx"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        super().__init__(rate_limiter, retry_policy)

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = OKX_MAX_CANDLES,
    ) -> list[OHLCVCandle]:
        canonical_symbol = symbol.upper()
        native_symbol = self._native_symbol(canonical_symbol)
        url = f"{OKX_PUBLIC_BASE}/api/v5/market/history-candles"
        params = {
            "instId": native_symbol,
            "bar": self._to_okx_bar(interval),
            "after": str(end_ms),
            "limit": str(min(limit, OKX_MAX_CANDLES)),
        }

        data = await self._get_okx_data(url, params)
        candles = [
            self._normalize_candle(row, canonical_symbol, interval)
            for row in data
            if start_ms <= int(row[0]) <= end_ms
        ]
        return sorted(candles, key=lambda candle: candle.timestamp_ms)

    async def fetch_funding(self, symbol: str, start_ms: int, end_ms: int) -> list[FundingRate]:
        canonical_symbol = symbol.upper()
        native_symbol = self._native_symbol(canonical_symbol)
        url = f"{OKX_PUBLIC_BASE}/api/v5/public/funding-rate-history"
        params = {
            "instId": native_symbol,
            "limit": "100",
        }

        data = await self._get_okx_data(url, params)
        rates = [
            self._normalize_funding(row, canonical_symbol)
            for row in data
            if start_ms <= int(row["fundingTime"]) <= end_ms
        ]
        return sorted(rates, key=lambda row: row.timestamp_ms)

    async def fetch_oi(self, symbol: str, interval: str = "snapshot") -> list[OpenInterest]:
        canonical_symbol = symbol.upper()
        native_symbol = self._native_symbol(canonical_symbol)
        url = f"{OKX_PUBLIC_BASE}/api/v5/public/open-interest"
        params = {
            "instType": "SWAP",
            "instId": native_symbol,
        }

        data = await self._get_okx_data(url, params)
        return [self._normalize_open_interest(row, canonical_symbol, interval) for row in data]

    async def fetch_liquidations(self, symbol: str, start_ms: int, end_ms: int) -> list[Liquidation]:
        """OKX public REST does not expose liquidation history in this adapter."""
        return []

    async def fetch_long_short_ratio(
        self, symbol: str, interval: str, start_ms: int, end_ms: int
    ) -> list[LongShortRatio]:
        canonical_symbol = symbol.upper()
        url = f"{OKX_PUBLIC_BASE}/api/v5/rubik/stat/contracts/long-short-account-ratio"
        params = {
            "ccy": canonical_symbol,
            "period": self._to_okx_period(interval),
        }

        data = await self._get_okx_data(url, params)
        ratios = [
            self._normalize_long_short(row, canonical_symbol, interval)
            for row in data
            if start_ms <= int(row[0]) <= end_ms
        ]
        return sorted(ratios, key=lambda row: row.timestamp_ms)

    async def health_check(self) -> ProviderHealthStatus:
        url = f"{OKX_PUBLIC_BASE}/api/v5/public/time"
        try:
            import time as _time

            t0 = _time.monotonic()
            resp = await self.client.get(url)
            latency = int((_time.monotonic() - t0) * 1000)
            data = resp.json()
            healthy = resp.status_code == 200 and data.get("code") == "0"
        except Exception as exc:
            return ProviderHealthStatus(
                source_name=self.source_name,
                is_healthy=False,
                last_error=str(exc),
                circuit_breaker_state=self.circuit_breaker.state.value,
            )

        return ProviderHealthStatus(
            source_name=self.source_name,
            is_healthy=healthy,
            latency_ms=latency,
            circuit_breaker_state=self.circuit_breaker.state.value,
        )

    async def _get_okx_data(self, url: str, params: dict[str, Any]) -> list[Any]:
        async def _do_request():
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            payload = resp.json()
            if payload.get("code") != "0":
                raise AdapterError(payload.get("msg") or f"OKX error code {payload.get('code')}")
            data = payload.get("data")
            return data if isinstance(data, list) else []

        return await self._execute_with_protection(_do_request)

    @staticmethod
    def _to_okx_bar(interval: str) -> str:
        mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1H",
            "2h": "2H",
            "4h": "4H",
            "6h": "6H",
            "12h": "12H",
            "1d": "1D",
        }
        return mapping.get(interval, interval)

    @staticmethod
    def _to_okx_period(interval: str) -> str:
        mapping = {
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1H",
            "2h": "2H",
            "4h": "4H",
            "1d": "1D",
        }
        return mapping.get(interval, "1H")

    @staticmethod
    def _normalize_candle(row: list[Any], symbol: str, interval: str) -> OHLCVCandle:
        return OHLCVCandle(
            timestamp_ms=int(row[0]),
            symbol=symbol,
            exchange="okx",
            interval=interval,
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[6]) if len(row) > 6 and row[6] not in (None, "") else float(row[5]),
            quote_volume=float(row[7]) if len(row) > 7 and row[7] not in (None, "") else None,
            trades_count=None,
        )

    @staticmethod
    def _normalize_funding(row: dict[str, Any], symbol: str) -> FundingRate:
        timestamp_ms = int(row["fundingTime"])
        return FundingRate(
            timestamp_ms=timestamp_ms,
            symbol=symbol,
            exchange="okx",
            funding_rate=float(row.get("realizedRate") or row.get("fundingRate") or 0),
            next_funding_time_ms=timestamp_ms + 8 * 60 * 60 * 1000,
            interval="8h",
        )

    @staticmethod
    def _normalize_open_interest(row: dict[str, Any], symbol: str, interval: str) -> OpenInterest:
        return OpenInterest(
            timestamp_ms=int(row["ts"]),
            symbol=symbol,
            exchange="okx",
            interval=interval,
            oi_usd=float(row.get("oiUsd") or 0),
            oi_coins=float(row.get("oiCcy") or 0),
        )

    @staticmethod
    def _normalize_long_short(row: list[Any], symbol: str, interval: str) -> LongShortRatio:
        ratio = float(row[1])
        long_share = ratio / (1 + ratio) if ratio > 0 else 0.0
        short_share = 1 / (1 + ratio) if ratio > 0 else 0.0
        return LongShortRatio(
            timestamp_ms=int(row[0]),
            symbol=symbol,
            exchange="okx",
            interval=interval,
            long_ratio=long_share,
            short_ratio=short_share,
            long_account_ratio=long_share,
            short_account_ratio=short_share,
        )

    @staticmethod
    def _native_symbol(canonical_symbol: str) -> str:
        try:
            return SymbolMapper().to_provider(canonical_symbol, "okx")
        except Exception:
            return f"{canonical_symbol}-USDT-SWAP"
