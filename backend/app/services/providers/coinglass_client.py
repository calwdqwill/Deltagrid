"""CoinGlass API client with rate-limit awareness and graceful fallback.

Docs: https://coinglass.readme.io/reference
"""

import asyncio
import logging
from typing import Optional, Any
from datetime import datetime, timezone

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://open-api-v4.coinglass.com"
DEFAULT_PERP_DEX_EXCHANGES = ("Aster", "Lighter", "EdgeX", "Drift")
COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES = (
    "Hyperliquid",
    "dYdX",
    "Aster",
    "Lighter",
    "EdgeX",
    "Drift",
    "Paradex",
    "Extended",
    "ApeX Omni",
)
PERP_DEX_ENRICHMENT_FIELD_GROUPS = {
    "price": ("mark_price",),
    "funding": ("funding_pct", "funding_rate"),
    "open_interest": ("open_interest_usd", "open_interest_base"),
    "volume": ("volume_24h_usd", "volume_24h_base"),
    "long_short": ("long_short_ratio_1h", "long_short_ratio_24h"),
    "liquidations": (
        "liquidation_usd_24h",
        "long_liquidation_usd_24h",
        "short_liquidation_usd_24h",
    ),
}


class CoinGlassClient:
    """Rate-limit aware CoinGlass client with retry and fallback."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.coinglass_standard_api_key or settings.coinglass_api_key
        self.base_url = (base_url or settings.coinglass_base_url).rstrip("/")
        self.client = httpx.AsyncClient(timeout=15.0, headers=self._headers())

    def _headers(self) -> dict:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            if "open-api-v4.coinglass.com" in self.base_url:
                headers["CG-API-KEY"] = self.api_key
            else:
                headers["coinglassSecret"] = self.api_key
        return headers

    async def close(self) -> None:
        await self.client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        if not self.api_key:
            logger.debug("CoinGlass API key not configured; skipping request")
            return None

        url = f"{self.base_url}{path}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"CoinGlass API error {e.response.status_code}: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.warning(f"CoinGlass request failed: {e}")
            return None

    @staticmethod
    def _extract_data(payload: Optional[dict]) -> Optional[Any]:
        if not payload:
            return None
        if payload.get("success") is True:
            return payload.get("data")
        if payload.get("code") in ("0", 0):
            return payload.get("data")
        return None

    async def get_funding_rates(
        self,
        symbol: Optional[str] = None,
        exchange_list: str = "Binance",
    ) -> Optional[list[dict]]:
        """Fetch funding rates. Returns list of funding rate entries."""
        params = {
            "exchange_list": exchange_list,
            "per_page": 100,
            "page": 1,
        }
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/coins-markets", params=params)
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        return None

    async def get_futures_coin_markets(
        self,
        symbol: Optional[str] = None,
        exchange_list: str = "Binance",
        per_page: int = 100,
        page: int = 1,
    ) -> Optional[list[dict]]:
        """Fetch CoinGlass futures coin market snapshots."""
        params = {
            "exchange_list": exchange_list,
            "per_page": min(max(per_page, 1), 100),
            "page": max(page, 1),
        }
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/coins-markets", params=params)
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        return None

    async def fetch_perp_dex_market_snapshot(
        self,
        symbols: tuple[str, ...],
        exchanges: tuple[str, ...] = DEFAULT_PERP_DEX_EXCHANGES,
    ) -> dict[str, Any]:
        """Fetch third-party CoinGlass Perp DEX enrichment rows.

        This is a research-only enrichment path. Rows are not execution-grade
        venue snapshots and must not be used for routing or liquidity ranking.
        """
        fetched_at = datetime.now(timezone.utc).isoformat()
        if not self.api_key:
            return self._empty_perp_dex_snapshot(symbols, exchanges, fetched_at, "auth_missing")

        async def fetch_exchange(exchange: str) -> tuple[str, Optional[list[dict]]]:
            return exchange, await self.get_futures_coin_markets(exchange_list=exchange)

        results = await asyncio.gather(*(fetch_exchange(exchange) for exchange in exchanges))
        rows_by_exchange = {
            exchange: rows
            for exchange, rows in results
            if rows is not None
        }
        errors = {
            exchange: "no_data_returned"
            for exchange, rows in results
            if rows is None
        }
        return self.normalize_perp_dex_market_snapshot(
            rows_by_exchange=rows_by_exchange,
            symbols=symbols,
            exchanges=exchanges,
            fetched_at=fetched_at,
            errors=errors,
        )

    @staticmethod
    def normalize_perp_dex_market_snapshot(
        rows_by_exchange: dict[str, list[dict]],
        symbols: tuple[str, ...],
        exchanges: tuple[str, ...],
        fetched_at: str,
        errors: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        symbol_set = {symbol.upper() for symbol in symbols}
        markets: list[dict[str, Any]] = []
        errors = errors or {}

        for exchange in exchanges:
            rows = rows_by_exchange.get(exchange) or []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                symbol = str(row.get("symbol", "")).upper()
                if symbol_set and symbol not in symbol_set:
                    continue

                funding_pct = _first_float(
                    row,
                    (
                        "avg_funding_rate_by_oi",
                        "avg_funding_rate_by_vol",
                        "fundingRate",
                        "funding_rate",
                    ),
                )
                premium_pct = _first_float(row, ("price_change_percent_24h", "priceChangePercent24h"))

                markets.append(
                    {
                        "symbol": symbol,
                        "market": f"{symbol}-PERP aggregate",
                        "venue_id": f"coinglass:{_venue_slug(exchange)}",
                        "venue_name": exchange,
                        "dex": exchange,
                        "status": "partial",
                        "provider_status": "third_party_aggregate",
                        "normalization_status": "coinglass_coin_market_enrichment",
                        "mark_price": _first_float(row, ("current_price", "currentPrice", "price")),
                        "mid_price": None,
                        "oracle_price": None,
                        "prev_day_price": None,
                        "funding_rate": funding_pct / 100 if funding_pct is not None else None,
                        "funding_pct": funding_pct,
                        "open_interest_base": _first_float(
                            row,
                            ("open_interest_quantity", "openInterestQuantity", "openInterest"),
                        ),
                        "open_interest_usd": _first_float(row, ("open_interest_usd", "openInterestUsd")),
                        "volume_24h_usd": _first_float(
                            row,
                            ("volume_24h_usd", "volume24hUsd", "volume_usd_24h", "volUsd24h"),
                        ),
                        "volume_24h_base": _first_float(row, ("volume_24h", "volume24h")),
                        "premium": None,
                        "premium_pct": premium_pct,
                        "impact_bid_price": None,
                        "impact_ask_price": None,
                        "only_isolated": False,
                        "max_leverage": None,
                        "sz_decimals": None,
                        "long_short_ratio_1h": _first_float(
                            row,
                            ("long_short_ratio_1h", "longShortRatio1h", "longShortRatio"),
                        ),
                        "long_short_ratio_24h": _first_float(
                            row,
                            ("long_short_ratio_24h", "longShortRatio24h"),
                        ),
                        "long_liquidation_usd_24h": _first_float(
                            row,
                            ("long_liquidation_usd_24h", "longLiquidationUsd24h", "longLiquidationUsd"),
                        ),
                        "short_liquidation_usd_24h": _first_float(
                            row,
                            ("short_liquidation_usd_24h", "shortLiquidationUsd24h", "shortLiquidationUsd"),
                        ),
                        "liquidation_usd_24h": _first_float(
                            row,
                            ("liquidation_usd_24h", "liquidationUsd24h", "liquidation_usd"),
                        ),
                        "open_interest_change_percent_24h": _first_float(
                            row,
                            ("open_interest_change_percent_24h", "openInterestChangePercent24h"),
                        ),
                        "volume_change_percent_24h": _first_float(
                            row,
                            ("volume_change_percent_24h", "volumeChangePercent24h"),
                        ),
                        "source_endpoint": "/api/futures/coins-markets",
                        "source_exchange": exchange,
                        "resolution_action": "validate direct venue adapter before route scoring",
                        "resolution_reason": (
                            "CoinGlass coin-level futures aggregates are useful for research enrichment, "
                            "but they are not execution-grade route inputs."
                        ),
                        "fetched_at": fetched_at,
                    }
                )

        markets.sort(key=lambda row: (row["venue_name"].lower(), row["symbol"]))
        coverage_summary = _build_perp_dex_enrichment_coverage(
            markets=markets,
            rows_by_exchange=rows_by_exchange,
            symbols=symbols,
            exchanges=exchanges,
            errors=errors,
        )
        if markets:
            status = "partial" if errors else "live"
            reason = None
        elif errors and len(errors) == len(exchanges):
            status = "unavailable"
            reason = "all_exchange_requests_failed"
        else:
            status = "empty"
            reason = "no_matching_rows"

        snapshot: dict[str, Any] = {
            "venue_id": "coinglass_perp_dex",
            "venue_name": "CoinGlass Perp DEX",
            "source": "coinglass_futures_coins_markets",
            "status": status,
            "dex": "coinglass",
            "requested_symbols": list(symbols),
            "requested_exchanges": list(exchanges),
            "candidate_exchanges": list(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES),
            "markets": markets,
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "normalization_status": "coinglass_coin_market_enrichment",
            "ranking_enabled": False,
            "production_signal_enabled": False,
            "coverage_summary": coverage_summary,
            "errors": errors,
        }
        if reason:
            snapshot["reason"] = reason
        return snapshot

    @staticmethod
    def _empty_perp_dex_snapshot(
        symbols: tuple[str, ...],
        exchanges: tuple[str, ...],
        fetched_at: str,
        reason: str,
    ) -> dict[str, Any]:
        return {
            "venue_id": "coinglass_perp_dex",
            "venue_name": "CoinGlass Perp DEX",
            "source": "coinglass_futures_coins_markets",
            "status": "unavailable",
            "dex": "coinglass",
            "requested_symbols": list(symbols),
            "requested_exchanges": list(exchanges),
            "candidate_exchanges": list(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "normalization_status": "coinglass_coin_market_enrichment",
            "ranking_enabled": False,
            "production_signal_enabled": False,
            "coverage_summary": _build_perp_dex_enrichment_coverage(
                markets=[],
                rows_by_exchange={},
                symbols=symbols,
                exchanges=exchanges,
                errors={exchange: reason for exchange in exchanges},
            ),
            "reason": reason,
        }

    async def get_open_interest(
        self,
        symbol: Optional[str] = None,
        exchange_list: str = "Binance",
    ) -> Optional[list[dict]]:
        """Fetch open interest."""
        params = {
            "exchange_list": exchange_list,
            "per_page": 100,
            "page": 1,
        }
        if symbol:
            params["symbol"] = symbol
        data = await self._request("GET", "/api/futures/coins-markets", params=params)
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        return None

    async def get_liquidation_aggregated_history(
        self,
        symbol: str,
        exchange_list: str = "Binance",
        interval: str = "1h",
        limit: int = 1000,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> Optional[list[dict]]:
        """Fetch aggregated long/short liquidation history for a futures coin."""
        params = {
            "exchange_list": exchange_list,
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time

        data = await self._request(
            "GET",
            "/api/futures/liquidation/aggregated-history",
            params=params,
        )
        rows = self._extract_data(data)
        if isinstance(rows, list):
            return rows
        if isinstance(rows, dict):
            for key in ("list", "items", "rows", "data"):
                nested = rows.get(key)
                if isinstance(nested, list):
                    return nested
        return None

    async def health_check(self) -> bool:
        """Quick health check."""
        if not self.api_key:
            return False
        data = await self._request(
            "GET",
            "/api/futures/coins-markets",
            params={"exchange_list": "Binance", "per_page": 1, "page": 1},
        )
        return self._extract_data(data) is not None


def _first_float(row: dict[str, Any], keys: tuple[str, ...]) -> Optional[float]:
    for key in keys:
        parsed = _to_float(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _to_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _venue_slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "_" for char in value.strip()).strip("_")


def _build_perp_dex_enrichment_coverage(
    markets: list[dict[str, Any]],
    rows_by_exchange: dict[str, list[dict]],
    symbols: tuple[str, ...],
    exchanges: tuple[str, ...],
    errors: dict[str, str],
) -> dict[str, Any]:
    requested_symbols = [symbol.upper() for symbol in symbols]
    by_exchange: dict[str, dict[str, Any]] = {}
    candidate_scores: list[tuple[int, int, int, str]] = []
    total_field_hits = {field_group: 0 for field_group in PERP_DEX_ENRICHMENT_FIELD_GROUPS}

    for exchange in exchanges:
        exchange_markets = [row for row in markets if row.get("source_exchange") == exchange]
        matched_symbols = sorted({str(row.get("symbol", "")).upper() for row in exchange_markets if row.get("symbol")})
        missing_symbols = [symbol for symbol in requested_symbols if symbol not in matched_symbols]
        field_hits = {
            field_group: sum(
                1
                for row in exchange_markets
                if any(row.get(field_name) is not None for field_name in field_names)
            )
            for field_group, field_names in PERP_DEX_ENRICHMENT_FIELD_GROUPS.items()
        }
        for field_group, count in field_hits.items():
            total_field_hits[field_group] += count

        available_field_groups = [
            field_group
            for field_group, count in field_hits.items()
            if count > 0
        ]
        if exchange in errors:
            status = "request_failed"
            next_action = "check CoinGlass exchange support or API plan before direct adapter review"
        elif not exchange_markets:
            status = "empty"
            next_action = "do not prioritize direct adapter from this CoinGlass sample yet"
        elif len(matched_symbols) == len(requested_symbols) and len(available_field_groups) >= 3:
            status = "screening_ready"
            next_action = "review official venue API and field semantics before direct adapter implementation"
        else:
            status = "partial"
            next_action = "expand symbols or verify missing fields before choosing direct adapter"

        by_exchange[exchange] = {
            "status": status,
            "requested_rows": len(rows_by_exchange.get(exchange, [])),
            "matched_rows": len(exchange_markets),
            "matched_symbols": matched_symbols,
            "missing_symbols": missing_symbols,
            "available_field_groups": available_field_groups,
            "field_coverage": field_hits,
            "route_input_status": "not_route_input",
            "next_action": next_action,
        }
        if exchange_markets:
            candidate_scores.append(
                (
                    len(matched_symbols),
                    len(available_field_groups),
                    len(exchange_markets),
                    exchange,
                )
            )

    candidate_scores.sort(reverse=True)
    direct_adapter_candidate_hints = [item[3] for item in candidate_scores]

    return {
        "requested_symbols": requested_symbols,
        "requested_exchanges": list(exchanges),
        "total_rows": len(markets),
        "exchanges_with_matches": sum(1 for row in by_exchange.values() if row["matched_rows"] > 0),
        "field_groups": list(PERP_DEX_ENRICHMENT_FIELD_GROUPS),
        "field_totals": total_field_hits,
        "direct_adapter_candidate_hints": direct_adapter_candidate_hints,
        "selection_policy": (
            "Coverage hints only; choose direct adapters after official venue API and field semantics review."
        ),
        "by_exchange": by_exchange,
    }
