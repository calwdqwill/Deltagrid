"""CoinGeckoDataAdapter — market data ingestion for CoinGecko Pro/Analyst API.

Endpoints:
- /coins/{id}/ohlc          — OHLCV (minutely/hourly/daily depending on plan)
- /coins/markets            — Market cap, volume, price change
- /coins/{id}               — Detailed coin data
"""

import logging
from typing import Optional

import httpx

from app.config import get_settings

from .base_adapter import BaseDataAdapter
from .data_models import OHLCVCandle, ProviderHealthStatus
from .data_writer import DataWriter
from .rate_limiter import GlobalRateLimiter, RetryPolicy
from .symbol_mapper import SymbolMapper

logger = logging.getLogger(__name__)

COIN_GECKO_PRO_BASE = "https://pro-api.coingecko.com/api/v3"
COIN_GECKO_DEMO_BASE = "https://api.coingecko.com/api/v3"


class CoinGeckoDataAdapter(BaseDataAdapter):
    """CoinGecko Analyst/Pro data adapter for OHLCV and market data."""

    source_name = "coingecko"

    def __init__(
        self,
        rate_limiter: GlobalRateLimiter,
        retry_policy: Optional[RetryPolicy] = None,
        symbol_mapper: Optional[SymbolMapper] = None,
        data_writer: Optional[DataWriter] = None,
    ):
        super().__init__(rate_limiter, retry_policy)
        settings = get_settings()
        self.api_key = settings.coingecko_api_key
        self.base_url = (
            settings.coingecko_pro_base_url
            if self.api_key
            else settings.coingecko_demo_base_url
        )
        self.symbol_mapper = symbol_mapper or SymbolMapper()
        self.writer = data_writer or DataWriter()

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        return headers

    def _params(self) -> dict:
        params = {}
        if self.api_key:
            params["x_cg_pro_api_key"] = self.api_key
        return params

    def _cg_id(self, canonical: str) -> str:
        """Resolve canonical symbol to CoinGecko coin ID."""
        try:
            return self.symbol_mapper.to_provider(
                canonical, "coingecko", alias_type="cg_id"
            )
        except ValueError:
            # Fallback: lowercase canonical as guess
            return canonical.lower()

    async def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1000,
    ) -> list[OHLCVCandle]:
        """Fetch OHLCV from CoinGecko /coins/{id}/ohlc.

        Note: CoinGecko OHLC endpoint does not support arbitrary start/end.
        It supports `days` parameter (1, 7, 14, 30, 90, 180, 365).
        For days=1 you may get minutely (Analyst+) or hourly (Demo).
        We translate start_ms/end_ms to the appropriate `days` value.
        """
        cg_id = self._cg_id(symbol)
        days = self._ms_to_days(end_ms - start_ms)

        url = f"{self.base_url}/coins/{cg_id}/ohlc"
        params = self._params()
        params.update({
            "vs_currency": "usd",
            "days": str(days),
        })

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        data = await self._execute_with_protection(_do_request)
        candles = [self._normalize_candle(raw, symbol, interval) for raw in data]

        # Detect granularity mismatch and log quality issue
        inferred_interval = self._infer_interval_from_candles(candles)
        if interval == "1m" and inferred_interval != "1m":
            self.writer.log_data_quality(
                table_name="ohlcv",
                check_type="granularity_fallback",
                severity="warning",
                symbol=symbol,
                exchange="coingecko",
                interval=interval,
                details_json=f'{{"requested_interval":"1m","actual_interval":"{inferred_interval}","days":{days}}}',
            )
            logger.warning(
                f"[CoinGecko] Requested 1m but got {inferred_interval} granularity for {symbol}"
            )

        # Filter by actual start/end since CG returns full history for `days`
        candles = [c for c in candles if start_ms <= c.timestamp_ms <= end_ms]
        return candles

    async def fetch_market_data(
        self,
        symbols: Optional[list[str]] = None,
        per_page: int = 20,
        page: int = 1,
    ) -> list[dict]:
        """Fetch market data from /coins/markets."""
        url = f"{self.base_url}/coins/markets"
        params = self._params()
        params.update({
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
        })
        if symbols:
            # CG markets endpoint accepts ids, not symbols
            # We attempt to map symbols -> cg_ids
            ids = []
            for s in symbols:
                try:
                    ids.append(self._cg_id(s))
                except ValueError:
                    ids.append(s.lower())
            params["ids"] = ",".join(ids)

        async def _do_request():
            resp = await self.client.get(url, headers=self._headers(), params=params)
            resp.raise_for_status()
            return resp.json()

        return await self._execute_with_protection(_do_request)

    async def fetch_funding(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """CoinGecko does not provide funding rates."""
        return []

    async def fetch_oi(self, symbol: str, interval: str = "1h") -> list:
        """CoinGecko does not provide open interest."""
        return []

    async def fetch_liquidations(self, symbol: str, start_ms: int, end_ms: int) -> list:
        """CoinGecko does not provide liquidation data."""
        return []

    async def fetch_long_short_ratio(
        self, symbol: str, interval: str, start_ms: int, end_ms: int
    ) -> list:
        """CoinGecko does not provide long/short ratio."""
        return []

    async def health_check(self) -> ProviderHealthStatus:
        url = f"{self.base_url}/ping"
        try:
            import time as _time
            t0 = _time.monotonic()
            resp = await self.client.get(url, headers=self._headers(), params=self._params())
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

    # -- Normalization -------------------------------------------------

    @staticmethod
    def _normalize_candle(raw: list, symbol: str, interval: str) -> OHLCVCandle:
        return OHLCVCandle(
            timestamp_ms=int(raw[0]),
            open=float(raw[1]),
            high=float(raw[2]),
            low=float(raw[3]),
            close=float(raw[4]),
            volume=0.0,  # CG /ohlc does not include volume
            quote_volume=None,
            trades_count=None,
            symbol=symbol,
            exchange="coingecko",
            interval=interval,
        )

    @staticmethod
    def _ms_to_days(delta_ms: int) -> int:
        """Map a time delta to the nearest supported `days` parameter."""
        days = max(1, delta_ms // 86_400_000)
        supported = [1, 7, 14, 30, 90, 180, 365]
        for d in supported:
            if days <= d:
                return d
        return 365

    @staticmethod
    def _infer_interval_from_candles(candles: list[OHLCVCandle]) -> str:
        """Infer actual interval from candle spacing."""
        if len(candles) < 2:
            return "unknown"
        delta = candles[1].timestamp_ms - candles[0].timestamp_ms
        if delta <= 120_000:
            return "1m"
        if delta <= 3_700_000:
            return "1h"
        return "1d"
