"""Read-only Aster public market data client."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://fapi.asterdex.com"
ORDERBOOK_DEPTH_LIMIT = 20
ORDERBOOK_DEPTH_TOP_N = 5


class AsterClient:
    """Small public client for Aster perpetual market snapshots."""

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
        exchange_info_response = await self.client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
        exchange_info_response.raise_for_status()
        exchange_info_payload = exchange_info_response.json()

        metadata_by_market = _metadata_by_market(exchange_info_payload)
        requested_markets = _requested_markets(metadata_by_market, symbols)

        premium_response, ticker_response, book_ticker_response = await asyncio.gather(
            self.client.get(f"{self.base_url}/fapi/v1/premiumIndex"),
            self.client.get(f"{self.base_url}/fapi/v1/ticker/24hr"),
            self.client.get(f"{self.base_url}/fapi/v1/ticker/bookTicker"),
        )
        premium_response.raise_for_status()
        ticker_response.raise_for_status()
        book_ticker_response.raise_for_status()

        async def fetch_open_interest(market: str) -> tuple[str, Any]:
            response = await self.client.get(f"{self.base_url}/fapi/v1/openInterest", params={"symbol": market})
            response.raise_for_status()
            return market, response.json()

        async def fetch_depth(market: str) -> tuple[str, Any]:
            response = await self.client.get(
                f"{self.base_url}/fapi/v3/depth",
                params={"symbol": market, "limit": ORDERBOOK_DEPTH_LIMIT},
            )
            response.raise_for_status()
            return market, response.json()

        open_interest_results, depth_results = await asyncio.gather(
            asyncio.gather(*(fetch_open_interest(market) for market in requested_markets)),
            asyncio.gather(*(fetch_depth(market) for market in requested_markets)),
        )

        return self.normalize_market_snapshot(
            exchange_info_payload=exchange_info_payload,
            premium_payload=premium_response.json(),
            ticker_payload=ticker_response.json(),
            book_ticker_payload=book_ticker_response.json(),
            open_interest_by_market={market: payload for market, payload in open_interest_results},
            symbols=symbols,
            depth_by_market={market: payload for market, payload in depth_results},
        )

    @staticmethod
    def normalize_market_snapshot(
        exchange_info_payload: Any,
        premium_payload: Any,
        ticker_payload: Any,
        book_ticker_payload: Any,
        open_interest_by_market: dict[str, dict[str, Any]],
        symbols: tuple[str, ...],
        depth_by_market: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
        fetched_at = datetime.now(timezone.utc).isoformat()
        metadata_by_market = _metadata_by_market(exchange_info_payload)
        if not metadata_by_market:
            return AsterClient._empty_snapshot(symbols, fetched_at, "missing_exchange_info")

        premium_by_market = _rows_by_market(premium_payload)
        ticker_by_market = _rows_by_market(ticker_payload)
        book_ticker_by_market = _rows_by_market(book_ticker_payload)

        markets: list[dict[str, Any]] = []
        for market, metadata in metadata_by_market.items():
            symbol = _canonical_symbol(str(metadata.get("baseAsset") or market))
            if symbol_set and symbol not in symbol_set:
                continue
            if str(metadata.get("contractType") or "").upper() != "PERPETUAL":
                continue
            if str(metadata.get("quoteAsset") or "").upper() != "USDT":
                continue

            premium = premium_by_market.get(market) or {}
            ticker = ticker_by_market.get(market) or {}
            book_ticker = book_ticker_by_market.get(market) or {}
            open_interest = open_interest_by_market.get(market) or {}
            depth_summary = _orderbook_depth_summary(
                (depth_by_market or {}).get(market),
                limit=ORDERBOOK_DEPTH_LIMIT,
                top_n=ORDERBOOK_DEPTH_TOP_N,
            )

            mark_price = _to_float(premium.get("markPrice"))
            bid_price = _to_float(book_ticker.get("bidPrice"))
            ask_price = _to_float(book_ticker.get("askPrice"))
            depth_spread_bps = depth_summary.get("top_of_book_spread_bps")
            mid_price = (
                (bid_price + ask_price) / 2
                if bid_price is not None and ask_price is not None
                else None
            )
            top_of_book_spread_bps = (
                depth_spread_bps
                if depth_spread_bps is not None
                else _top_of_book_spread_bps(bid_price, ask_price)
            )
            funding_rate = _to_float(premium.get("lastFundingRate"))
            open_interest_base = _to_float(open_interest.get("openInterest"))
            open_interest_usd = (
                open_interest_base * mark_price
                if open_interest_base is not None and mark_price is not None
                else None
            )

            filters = metadata.get("filters") if isinstance(metadata.get("filters"), list) else []
            price_filter = _filter_by_type(filters, "PRICE_FILTER")
            lot_size_filter = _filter_by_type(filters, "LOT_SIZE")
            min_notional_filter = _filter_by_type(filters, "MIN_NOTIONAL")

            markets.append(
                {
                    "symbol": symbol,
                    "market": market,
                    "venue_id": "aster",
                    "venue_name": "Aster",
                    "dex": None,
                    "status": "live" if _status_trading(metadata.get("status")) and mark_price is not None else "partial",
                    "provider_status": metadata.get("status"),
                    "normalization_status": "aster_public_futures_market_data",
                    "mark_price": mark_price,
                    "mid_price": mid_price,
                    "oracle_price": _to_float(premium.get("indexPrice")),
                    "prev_day_price": _to_float(ticker.get("openPrice")),
                    "price_source": "markPrice",
                    "price_change_24h": _to_float(ticker.get("priceChange")),
                    "price_change_percent_24h": _to_float(ticker.get("priceChangePercent")),
                    "funding_rate": funding_rate,
                    "funding_pct": funding_rate * 100 if funding_rate is not None else None,
                    "interest_rate": _to_float(premium.get("interestRate")),
                    "next_funding_time": premium.get("nextFundingTime"),
                    "open_interest_base": open_interest_base,
                    "open_interest_usd": open_interest_usd,
                    "volume_24h_usd": _to_float(ticker.get("quoteVolume")),
                    "volume_24h_base": _to_float(ticker.get("volume")),
                    "trades_24h": _to_int(ticker.get("count")),
                    "premium": None,
                    "premium_pct": None,
                    "impact_bid_price": None,
                    "impact_ask_price": None,
                    "bid_price": bid_price,
                    "ask_price": ask_price,
                    "bid_qty": _to_float(book_ticker.get("bidQty")),
                    "ask_qty": _to_float(book_ticker.get("askQty")),
                    **depth_summary,
                    "top_of_book_spread_bps": top_of_book_spread_bps,
                    "top_of_book_spread_status": (
                        "display_only"
                        if top_of_book_spread_bps is not None
                        else "missing_bid_ask"
                    ),
                    "only_isolated": False,
                    "max_leverage": None,
                    "sz_decimals": None,
                    "liquidation_fee": _to_float(metadata.get("liquidationFee")),
                    "market_take_bound": _to_float(metadata.get("marketTakeBound")),
                    "tick_size": _to_float(price_filter.get("tickSize")),
                    "step_size": _to_float(lot_size_filter.get("stepSize")),
                    "min_base_amount": _to_float(lot_size_filter.get("minQty")),
                    "min_quote_amount": _to_float(min_notional_filter.get("notional")),
                    "source_endpoint": (
                        "/fapi/v1/exchangeInfo + /fapi/v1/premiumIndex + /fapi/v1/ticker/24hr "
                        "+ /fapi/v1/openInterest + /fapi/v1/ticker/bookTicker + /fapi/v3/depth"
                    ),
                    "resolution_action": "source fee/depth semantics before route scoring",
                    "resolution_reason": "public futures market data and top depth levels are read-only diagnostics, not execution-grade routing input",
                    "fetched_at": fetched_at,
                }
            )

        markets.sort(key=lambda item: item["symbol"])
        return {
            "venue_id": "aster",
            "venue_name": "Aster",
            "source": "aster_fapi_public_market_data",
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
            "venue_id": "aster",
            "venue_name": "Aster",
            "source": "aster_fapi_public_market_data",
            "status": "empty",
            "dex": None,
            "requested_symbols": list(symbols),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "reason": reason,
        }


def _metadata_by_market(payload: Any) -> dict[str, dict[str, Any]]:
    rows = payload.get("symbols") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {}

    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        market = str(row.get("symbol") or "").upper()
        if market:
            result[market] = row
    return result


def _requested_markets(metadata_by_market: dict[str, dict[str, Any]], symbols: tuple[str, ...]) -> list[str]:
    symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
    requested: list[str] = []
    for market, metadata in metadata_by_market.items():
        symbol = _canonical_symbol(str(metadata.get("baseAsset") or market))
        if symbol_set and symbol not in symbol_set:
            continue
        if str(metadata.get("contractType") or "").upper() != "PERPETUAL":
            continue
        if str(metadata.get("quoteAsset") or "").upper() != "USDT":
            continue
        requested.append(market)
    return requested


def _rows_by_market(payload: Any) -> dict[str, dict[str, Any]]:
    rows = payload if isinstance(payload, list) else [payload]
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        market = str(row.get("symbol") or "").upper()
        if market:
            result[market] = row
    return result


def _filter_by_type(filters: list[Any], filter_type: str) -> dict[str, Any]:
    for row in filters:
        if isinstance(row, dict) and row.get("filterType") == filter_type:
            return row
    return {}


def _canonical_symbol(value: str) -> str:
    normalized = value.strip().upper()
    for suffix in ("-USDT", "-USD", "/USDT", "/USD", "-PERP", "USDT", "USD"):
        if normalized.endswith(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _status_trading(value: Any) -> bool:
    return str(value or "").upper() == "TRADING"


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


def _orderbook_depth_summary(payload: Any, limit: int, top_n: int) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "orderbook_depth_status": "missing_fapi_v3_depth",
            "orderbook_order_limit": limit,
            "orderbook_depth_safe_use": "Aster depth ladder unavailable; do not infer slippage or executable liquidity",
        }

    bids = _parse_depth_levels(payload.get("bids"), reverse=True)
    asks = _parse_depth_levels(payload.get("asks"), reverse=False)
    best_bid = bids[0] if bids else None
    best_ask = asks[0] if asks else None
    bid_top = bids[:top_n]
    ask_top = asks[:top_n]

    if bids and asks:
        status = "partial_ready_depth_ladder_display_only"
    elif bids or asks:
        status = "partial_ready_one_sided_depth_ladder_display_only"
    else:
        status = "empty_depth_ladder"

    return {
        "orderbook_depth_status": status,
        "orderbook_order_limit": limit,
        "orderbook_bid_orders": len(bids),
        "orderbook_ask_orders": len(asks),
        "best_bid_price": best_bid["price"] if best_bid else None,
        "best_ask_price": best_ask["price"] if best_ask else None,
        "best_bid_size_base": best_bid["size_base"] if best_bid else None,
        "best_ask_size_base": best_ask["size_base"] if best_ask else None,
        "top_of_book_spread_bps": _top_of_book_spread_bps(
            best_bid["price"] if best_bid else None,
            best_ask["price"] if best_ask else None,
        ),
        "bid_depth_top_orders_base": _sum_field(bid_top, "size_base"),
        "ask_depth_top_orders_base": _sum_field(ask_top, "size_base"),
        "bid_depth_top_orders_usd": _sum_field(bid_top, "notional_usd"),
        "ask_depth_top_orders_usd": _sum_field(ask_top, "notional_usd"),
        "orderbook_top_bid_orders": bid_top,
        "orderbook_top_ask_orders": ask_top,
        "orderbook_depth_safe_use": (
            "display Aster /fapi/v3/depth top levels only; do not treat as executable "
            "slippage without order size, aggregation policy, liquidity caps and stale-depth handling"
        ),
    }


def _parse_depth_levels(rows: Any, reverse: bool) -> list[dict[str, float]]:
    if not isinstance(rows, list):
        return []

    levels: list[dict[str, float]] = []
    for row in rows:
        if not isinstance(row, list) or len(row) < 2:
            continue
        price = _to_float(row[0])
        size_base = _to_float(row[1])
        if price is None or size_base is None or price <= 0 or size_base <= 0:
            continue
        levels.append(
            {
                "price": price,
                "size_base": size_base,
                "notional_usd": price * size_base,
            }
        )

    levels.sort(key=lambda item: item["price"], reverse=reverse)
    return levels


def _sum_field(rows: list[dict[str, float]], field: str) -> Optional[float]:
    if not rows:
        return None
    return sum(row[field] for row in rows)


def _top_of_book_spread_bps(bid_price: Optional[float], ask_price: Optional[float]) -> Optional[float]:
    if bid_price is None or ask_price is None:
        return None
    if bid_price <= 0 or ask_price <= 0 or ask_price < bid_price:
        return None
    mid_price = (bid_price + ask_price) / 2
    if mid_price <= 0:
        return None
    return ((ask_price - bid_price) / mid_price) * 10_000
