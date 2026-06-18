"""Read-only Lighter public market data client."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://mainnet.zklighter.elliot.ai/api/v1"
ORDERBOOK_ORDERS_LIMIT = 25
ORDERBOOK_DEPTH_TOP_N = 5


class LighterClient:
    """Small public client for Lighter perpetual market snapshots."""

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
        order_books_response = await self.client.get(f"{self.base_url}/orderBooks")
        order_books_response.raise_for_status()
        order_books_payload = order_books_response.json()

        metadata_by_symbol = _metadata_by_symbol(order_books_payload)
        symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
        selected_metadata = [
            metadata
            for symbol, metadata in metadata_by_symbol.items()
            if not symbol_set or symbol in symbol_set
        ]

        async def fetch_details(market_id: int) -> tuple[int, Any]:
            response = await self.client.get(f"{self.base_url}/orderBookDetails", params={"market_id": market_id})
            response.raise_for_status()
            return market_id, response.json()

        async def fetch_orders(market_id: int) -> tuple[int, Any]:
            response = await self.client.get(
                f"{self.base_url}/orderBookOrders",
                params={"market_id": market_id, "limit": ORDERBOOK_ORDERS_LIMIT},
            )
            response.raise_for_status()
            return market_id, response.json()

        detail_results = await asyncio.gather(
            *(
                fetch_details(market_id)
                for metadata in selected_metadata
                if (market_id := _to_int(metadata.get("market_id"))) is not None
            )
        )
        details_by_market_id = {
            market_id: _first_detail(payload)
            for market_id, payload in detail_results
        }
        order_results = await asyncio.gather(
            *(
                fetch_orders(market_id)
                for metadata in selected_metadata
                if (market_id := _to_int(metadata.get("market_id"))) is not None
            )
        )
        orders_by_market_id = {
            market_id: payload
            for market_id, payload in order_results
        }

        funding_response = await self.client.get(f"{self.base_url}/funding-rates")
        funding_response.raise_for_status()
        funding_by_market_id = _funding_by_market_id(funding_response.json())

        return self.normalize_market_snapshot(
            order_books_payload=order_books_payload,
            details_by_market_id=details_by_market_id,
            orders_by_market_id=orders_by_market_id,
            funding_by_market_id=funding_by_market_id,
            symbols=symbols,
        )

    @staticmethod
    def normalize_market_snapshot(
        order_books_payload: Any,
        details_by_market_id: dict[int, dict[str, Any]],
        funding_by_market_id: dict[int, float],
        symbols: tuple[str, ...],
        orders_by_market_id: Optional[dict[int, Any]] = None,
    ) -> dict[str, Any]:
        symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
        fetched_at = datetime.now(timezone.utc).isoformat()
        metadata_by_symbol = _metadata_by_symbol(order_books_payload)
        if not metadata_by_symbol:
            return LighterClient._empty_snapshot(symbols, fetched_at, "missing_order_books")

        markets: list[dict[str, Any]] = []
        for symbol, metadata in metadata_by_symbol.items():
            if symbol_set and symbol not in symbol_set:
                continue
            if str(metadata.get("market_type") or "").lower() != "perp":
                continue

            market_id = _to_int(metadata.get("market_id"))
            market_key = market_id if market_id is not None else -1
            details = details_by_market_id.get(market_key) or {}
            row = {**metadata, **details}
            depth_summary = _orderbook_depth_summary(
                (orders_by_market_id or {}).get(market_key),
                limit=ORDERBOOK_ORDERS_LIMIT,
                top_n=ORDERBOOK_DEPTH_TOP_N,
            )

            last_trade_price = _to_float(row.get("last_trade_price"))
            open_interest_base = _to_float(row.get("open_interest"))
            open_interest_usd = (
                open_interest_base * last_trade_price
                if open_interest_base is not None and last_trade_price is not None
                else None
            )
            funding_rate = funding_by_market_id.get(market_key)
            initial_margin_fraction = _margin_fraction(row.get("default_initial_margin_fraction"))

            markets.append(
                {
                    "symbol": symbol,
                    "market": f"{symbol}-PERP",
                    "venue_id": "lighter",
                    "venue_name": "Lighter",
                    "dex": None,
                    "status": "live" if _status_active(row.get("status")) and last_trade_price is not None else "partial",
                    "provider_status": row.get("status"),
                    "normalization_status": "lighter_public_market_details",
                    "mark_price": last_trade_price,
                    "mid_price": None,
                    "oracle_price": None,
                    "prev_day_price": None,
                    "price_source": "last_trade_price",
                    "price_change_24h": _to_float(row.get("daily_price_change")),
                    "funding_rate": funding_rate,
                    "funding_pct": funding_rate * 100 if funding_rate is not None else None,
                    "open_interest_base": open_interest_base,
                    "open_interest_usd": open_interest_usd,
                    "volume_24h_usd": _to_float(row.get("daily_quote_token_volume")),
                    "volume_24h_base": _to_float(row.get("daily_base_token_volume")),
                    "trades_24h": _to_int(row.get("daily_trades_count")),
                    "premium": None,
                    "premium_pct": None,
                    "impact_bid_price": None,
                    "impact_ask_price": None,
                    "only_isolated": False,
                    "max_leverage": _max_leverage(initial_margin_fraction),
                    "initial_margin_fraction": initial_margin_fraction,
                    "maintenance_margin_fraction": _margin_fraction(row.get("maintenance_margin_fraction")),
                    "maker_fee": _to_float(row.get("maker_fee")),
                    "taker_fee": _to_float(row.get("taker_fee")),
                    "liquidation_fee": _to_float(row.get("liquidation_fee")),
                    **depth_summary,
                    "min_base_amount": _to_float(row.get("min_base_amount")),
                    "min_quote_amount": _to_float(row.get("min_quote_amount")),
                    "tick_size": _tick_size(row.get("supported_price_decimals")),
                    "step_size": _tick_size(row.get("supported_size_decimals")),
                    "market_id": market_id,
                    "market_type": row.get("market_type"),
                    "source_endpoint": "/api/v1/orderBooks + /api/v1/orderBookDetails + /api/v1/orderBookOrders + /api/v1/funding-rates",
                    "resolution_action": "confirm order intent, aggregation policy and slippage math before route scoring",
                    "resolution_reason": "public market details and top order depth are read-only diagnostics, not execution-grade routing input",
                    "fetched_at": fetched_at,
                }
            )

        markets.sort(key=lambda item: item["symbol"])
        return {
            "venue_id": "lighter",
            "venue_name": "Lighter",
            "source": "lighter_order_books_details",
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
            "venue_id": "lighter",
            "venue_name": "Lighter",
            "source": "lighter_order_books_details",
            "status": "empty",
            "dex": None,
            "requested_symbols": list(symbols),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "reason": reason,
        }


def _metadata_by_symbol(payload: Any) -> dict[str, dict[str, Any]]:
    rows = payload.get("order_books") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {}

    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        symbol = _canonical_symbol(str(row.get("symbol") or ""))
        if symbol:
            result[symbol] = row
    return result


def _first_detail(payload: Any) -> dict[str, Any]:
    rows = payload.get("order_book_details") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        return {}
    first = rows[0]
    return first if isinstance(first, dict) else {}


def _funding_by_market_id(payload: Any) -> dict[int, float]:
    rows = payload.get("funding_rates") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {}

    result: dict[int, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("exchange") or "").lower() != "lighter":
            continue
        market_id = _to_int(row.get("market_id"))
        rate = _to_float(row.get("rate"))
        if market_id is not None and rate is not None:
            result[market_id] = rate
    return result


def _orderbook_depth_summary(payload: Any, limit: int, top_n: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "orderbook_depth_status": "missing_orderbook_orders",
            "orderbook_order_limit": limit,
            "orderbook_depth_safe_use": "no orderBookOrders payload available; do not estimate slippage",
        }

    bids = _parse_depth_orders(payload.get("bids"), reverse=True)
    asks = _parse_depth_orders(payload.get("asks"), reverse=False)
    best_bid = bids[0] if bids else None
    best_ask = asks[0] if asks else None
    best_bid_price = best_bid["price"] if best_bid else None
    best_ask_price = best_ask["price"] if best_ask else None
    spread_bps = _top_of_book_spread_bps(best_bid_price, best_ask_price)
    top_bids = bids[:top_n]
    top_asks = asks[:top_n]

    if bids and asks:
        status = "partial_ready_top_orders_only"
    elif bids or asks:
        status = "partial_ready_one_sided_top_orders_only"
    else:
        status = "empty_orderbook_orders"

    return {
        "orderbook_depth_status": status,
        "orderbook_order_limit": limit,
        "orderbook_bid_orders": len(bids),
        "orderbook_ask_orders": len(asks),
        "best_bid_price": best_bid_price,
        "best_ask_price": best_ask_price,
        "best_bid_size_base": best_bid["size_base"] if best_bid else None,
        "best_ask_size_base": best_ask["size_base"] if best_ask else None,
        "top_of_book_spread_bps": spread_bps,
        "bid_depth_top_orders_base": _sum_field(top_bids, "size_base"),
        "ask_depth_top_orders_base": _sum_field(top_asks, "size_base"),
        "bid_depth_top_orders_usd": _sum_field(top_bids, "notional_usd"),
        "ask_depth_top_orders_usd": _sum_field(top_asks, "notional_usd"),
        "orderbook_top_bid_orders": top_bids,
        "orderbook_top_ask_orders": top_asks,
        "orderbook_depth_safe_use": "display top resting orders only; do not infer executable slippage without order size, aggregation policy and route risk limits",
    }


def _parse_depth_orders(rows: Any, reverse: bool) -> list[dict[str, float]]:
    if not isinstance(rows, list):
        return []

    parsed: list[dict[str, float]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        price = _to_float(row.get("price"))
        size_base = _to_float(row.get("remaining_base_amount"))
        if price is None or size_base is None or price <= 0 or size_base < 0:
            continue
        parsed.append(
            {
                "price": price,
                "size_base": size_base,
                "notional_usd": price * size_base,
            }
        )
    return sorted(parsed, key=lambda item: item["price"], reverse=reverse)


def _sum_field(rows: list[dict[str, float]], field: str) -> Optional[float]:
    if not rows:
        return None
    return sum(row[field] for row in rows)


def _top_of_book_spread_bps(best_bid_price: Optional[float], best_ask_price: Optional[float]) -> Optional[float]:
    if best_bid_price is None or best_ask_price is None:
        return None
    if best_bid_price <= 0 or best_ask_price <= 0 or best_ask_price < best_bid_price:
        return None
    mid_price = (best_bid_price + best_ask_price) / 2
    if mid_price <= 0:
        return None
    return ((best_ask_price - best_bid_price) / mid_price) * 10_000


def _canonical_symbol(value: str) -> str:
    normalized = value.strip().upper()
    for suffix in ("-USD", "-USDT", "/USD", "/USDT", "-PERP"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _status_active(value: Any) -> bool:
    return str(value or "").lower() == "active"


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


def _margin_fraction(value: Any) -> Optional[float]:
    parsed = _to_float(value)
    if parsed is None:
        return None
    if parsed > 1:
        return parsed / 10_000
    return parsed


def _max_leverage(initial_margin_fraction: Optional[float]) -> Optional[int]:
    if initial_margin_fraction is None or initial_margin_fraction <= 0:
        return None
    return int(1 / initial_margin_fraction)


def _tick_size(decimals: Any) -> Optional[float]:
    parsed = _to_int(decimals)
    if parsed is None or parsed < 0:
        return None
    return 10 ** (-parsed)
