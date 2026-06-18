"""Read-only Hyperliquid public market data client."""

from datetime import datetime, timezone
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://api.hyperliquid.xyz"


class HyperliquidClient:
    """Small public client for Hyperliquid market snapshots."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def fetch_market_snapshot(self, symbols: tuple[str, ...], dex: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"type": "metaAndAssetCtxs"}
        if dex:
            payload["dex"] = dex

        response = await self.client.post(f"{self.base_url}/info", json=payload)
        response.raise_for_status()

        return self.normalize_market_snapshot(response.json(), symbols=symbols, dex=dex)

    @staticmethod
    def normalize_market_snapshot(payload: Any, symbols: tuple[str, ...], dex: str = "") -> dict[str, Any]:
        symbol_set = {symbol.upper() for symbol in symbols}
        fetched_at = datetime.now(timezone.utc).isoformat()
        markets: list[dict[str, Any]] = []

        if not isinstance(payload, list) or len(payload) < 2:
            return HyperliquidClient._empty_snapshot(symbols, dex, fetched_at, "unexpected_payload")

        meta = payload[0] if isinstance(payload[0], dict) else {}
        contexts = payload[1] if isinstance(payload[1], list) else []
        universe = meta.get("universe") if isinstance(meta, dict) else None
        if not isinstance(universe, list):
            return HyperliquidClient._empty_snapshot(symbols, dex, fetched_at, "missing_universe")

        for index, asset in enumerate(universe):
            if not isinstance(asset, dict):
                continue
            symbol = str(asset.get("name") or "").upper()
            if symbol_set and symbol not in symbol_set:
                continue

            context = contexts[index] if index < len(contexts) and isinstance(contexts[index], dict) else {}
            mark_price = _to_float(context.get("markPx"))
            mid_price = _to_float(context.get("midPx"))
            oracle_price = _to_float(context.get("oraclePx"))
            prev_day_price = _to_float(context.get("prevDayPx"))
            funding_rate = _to_float(context.get("funding"))
            premium = _to_float(context.get("premium"))
            impact_prices = context.get("impactPxs")
            open_interest_base = _to_float(context.get("openInterest"))
            open_interest_usd = (
                open_interest_base * mark_price
                if open_interest_base is not None and mark_price is not None
                else None
            )

            markets.append(
                {
                    "symbol": symbol,
                    "market": f"{symbol}-PERP",
                    "venue_id": "hyperliquid",
                    "venue_name": "Hyperliquid",
                    "dex": dex or None,
                    "status": "live" if mark_price is not None or mid_price is not None else "partial",
                    "mark_price": mark_price,
                    "mid_price": mid_price,
                    "oracle_price": oracle_price,
                    "prev_day_price": prev_day_price,
                    "funding_rate": funding_rate,
                    "funding_pct": funding_rate * 100 if funding_rate is not None else None,
                    "open_interest_base": open_interest_base,
                    "open_interest_usd": open_interest_usd,
                    "volume_24h_usd": _to_float(context.get("dayNtlVlm")),
                    "volume_24h_base": _to_float(context.get("dayBaseVlm")),
                    "premium": premium,
                    "premium_pct": premium * 100 if premium is not None else None,
                    "impact_bid_price": _impact_price(impact_prices, 0),
                    "impact_ask_price": _impact_price(impact_prices, 1),
                    "only_isolated": bool(asset.get("onlyIsolated")) if "onlyIsolated" in asset else False,
                    "max_leverage": _to_int(asset.get("maxLeverage")),
                    "sz_decimals": _to_int(asset.get("szDecimals")),
                    "fetched_at": fetched_at,
                }
            )

        markets.sort(key=lambda row: row["symbol"])
        return {
            "venue_id": "hyperliquid",
            "venue_name": "Hyperliquid",
            "source": "hyperliquid_info_metaAndAssetCtxs",
            "status": "live" if markets else "empty",
            "dex": dex or None,
            "requested_symbols": list(symbols),
            "markets": markets,
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
        }

    @staticmethod
    def _empty_snapshot(symbols: tuple[str, ...], dex: str, fetched_at: str, reason: str) -> dict[str, Any]:
        return {
            "venue_id": "hyperliquid",
            "venue_name": "Hyperliquid",
            "source": "hyperliquid_info_metaAndAssetCtxs",
            "status": "empty",
            "dex": dex or None,
            "requested_symbols": list(symbols),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "reason": reason,
        }


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


def _impact_price(values: Any, index: int) -> Optional[float]:
    if not isinstance(values, list) or len(values) <= index:
        return None
    return _to_float(values[index])
