"""Read-only dYdX Indexer market data client."""

from datetime import datetime, timezone
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://indexer.dydx.trade/v4"


class DydxClient:
    """Small public client for dYdX v4 perpetual market snapshots."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(
            timeout=10.0,
            headers={"Accept": "application/json", "User-Agent": "DeltaGridBackend/1.0"},
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def fetch_market_snapshot(self, symbols: tuple[str, ...]) -> dict[str, Any]:
        response = await self.client.get(f"{self.base_url}/perpetualMarkets")
        response.raise_for_status()

        return self.normalize_market_snapshot(response.json(), symbols=symbols)

    @staticmethod
    def normalize_market_snapshot(payload: Any, symbols: tuple[str, ...]) -> dict[str, Any]:
        symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
        fetched_at = datetime.now(timezone.utc).isoformat()
        markets_payload = payload.get("markets") if isinstance(payload, dict) else None
        if not isinstance(markets_payload, dict):
            return DydxClient._empty_snapshot(symbols, fetched_at, "missing_markets")

        markets: list[dict[str, Any]] = []
        for market_key, row in markets_payload.items():
            if not isinstance(row, dict):
                continue
            ticker = str(row.get("ticker") or market_key).upper()
            symbol = _canonical_symbol(ticker)
            if symbol_set and symbol not in symbol_set:
                continue

            oracle_price = _to_float(row.get("oraclePrice"))
            price_change_24h = _to_float(row.get("priceChange24H"))
            funding_rate = _to_float(row.get("nextFundingRate"))
            open_interest_base = _to_float(row.get("openInterest"))
            open_interest_usd = (
                open_interest_base * oracle_price
                if open_interest_base is not None and oracle_price is not None
                else None
            )

            markets.append(
                {
                    "symbol": symbol,
                    "market": ticker,
                    "venue_id": "dydx",
                    "venue_name": "dYdX",
                    "dex": None,
                    "status": "live" if str(row.get("status") or "").upper() == "ACTIVE" else "partial",
                    "provider_status": row.get("status"),
                    "mark_price": oracle_price,
                    "mid_price": None,
                    "oracle_price": oracle_price,
                    "prev_day_price": oracle_price - price_change_24h
                    if oracle_price is not None and price_change_24h is not None
                    else None,
                    "price_change_24h": price_change_24h,
                    "funding_rate": funding_rate,
                    "funding_pct": funding_rate * 100 if funding_rate is not None else None,
                    "open_interest_base": open_interest_base,
                    "open_interest_usd": open_interest_usd,
                    "volume_24h_usd": _to_float(row.get("volume24H")),
                    "volume_24h_base": None,
                    "trades_24h": _to_int(row.get("trades24H")),
                    "premium": None,
                    "premium_pct": None,
                    "impact_bid_price": None,
                    "impact_ask_price": None,
                    "only_isolated": False,
                    "max_leverage": _max_leverage(row.get("initialMarginFraction")),
                    "initial_margin_fraction": _to_float(row.get("initialMarginFraction")),
                    "maintenance_margin_fraction": _to_float(row.get("maintenanceMarginFraction")),
                    "tick_size": _to_float(row.get("tickSize")),
                    "step_size": _to_float(row.get("stepSize")),
                    "market_type": row.get("marketType"),
                    "fetched_at": fetched_at,
                }
            )

        markets.sort(key=lambda item: item["symbol"])
        return {
            "venue_id": "dydx",
            "venue_name": "dYdX",
            "source": "dydx_indexer_perpetualMarkets",
            "status": "live" if markets else "empty",
            "dex": None,
            "requested_symbols": list(symbols),
            "markets": markets,
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
        }

    @staticmethod
    def _empty_snapshot(symbols: tuple[str, ...], fetched_at: str, reason: str) -> dict[str, Any]:
        return {
            "venue_id": "dydx",
            "venue_name": "dYdX",
            "source": "dydx_indexer_perpetualMarkets",
            "status": "empty",
            "dex": None,
            "requested_symbols": list(symbols),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "reason": reason,
        }


def _canonical_symbol(value: str) -> str:
    normalized = value.strip().upper()
    for suffix in ("-USD", "-USDT", "/USD", "/USDT", "-PERP"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _to_float(value: Any) -> Optional[float]:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _max_leverage(initial_margin_fraction: Any) -> Optional[int]:
    value = _to_float(initial_margin_fraction)
    if value is None or value <= 0:
        return None
    return int(1 / value)
