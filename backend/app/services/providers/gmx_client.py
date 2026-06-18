"""Read-only GMX public market data client."""

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import httpx

DEFAULT_BASE_URL = "https://arbitrum-api.gmxinfra.io"

RAW_METRIC_FIELDS = (
    "openInterestLong",
    "openInterestShort",
    "availableLiquidityLong",
    "availableLiquidityShort",
    "poolAmountLong",
    "poolAmountShort",
    "fundingRateLong",
    "fundingRateShort",
    "borrowingRateLong",
    "borrowingRateShort",
    "netRateLong",
    "netRateShort",
)

GMX_USD_DECIMALS = 30
GMX_RATE_PERIOD = "1h"
GMX_RATE_SEMANTICS_SOURCE = "gmx_interface_market_ticker_hourly_rates"
GMX_RATE_RELATIONS = {
    "long": ("fundingRateLong", "borrowingRateLong", "netRateLong"),
    "short": ("fundingRateShort", "borrowingRateShort", "netRateShort"),
}
GMX_RATE_SOURCE_FIELDS = (
    "fundingFactorPerSecond",
    "borrowingFactorPerSecondForLongs",
    "borrowingFactorPerSecondForShorts",
    "longsPayShorts",
)
GMX_RATE_STATUS_MINUS = "net_equals_funding_minus_borrowing"
GMX_RATE_STATUS_PLUS = "net_equals_funding_plus_borrowing"
GMX_RATE_STATUS_ZERO_BORROWING = "net_equals_funding_with_zero_borrowing"


class GmxClient:
    """Small public client for GMX market snapshots.

    GMX REST market info exposes several fixed-point/token-unit fields. This v0
    adapter intentionally preserves those fields as raw strings until scales and
    token decimals are validated for production liquidity/OI calculations.
    """

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
        markets_response = await self.client.get(f"{self.base_url}/markets/info")
        markets_response.raise_for_status()
        tokens_response = await self.client.get(f"{self.base_url}/tokens")
        tokens_response.raise_for_status()

        return self.normalize_market_snapshot(
            markets_response.json(),
            symbols=symbols,
            token_payload=tokens_response.json(),
        )

    @staticmethod
    def normalize_market_snapshot(
        payload: Any,
        symbols: tuple[str, ...],
        token_payload: Any = None,
    ) -> dict[str, Any]:
        symbol_set = {_canonical_symbol(symbol) for symbol in symbols}
        fetched_at = datetime.now(timezone.utc).isoformat()
        token_metadata = _token_metadata_by_address(token_payload)
        markets_payload = payload.get("markets") if isinstance(payload, dict) else None
        if not isinstance(markets_payload, list):
            return GmxClient._empty_snapshot(symbols, fetched_at, "missing_markets")

        markets: list[dict[str, Any]] = []
        for row in markets_payload:
            if not isinstance(row, dict):
                continue

            symbol = _market_symbol(row)
            if symbol_set and symbol not in symbol_set:
                continue

            name = _string_or_none(row.get("name")) or f"{symbol}/USD"
            raw_metrics = {field: _string_or_none(row.get(field)) for field in RAW_METRIC_FIELDS if row.get(field) not in (None, "")}
            is_disabled = _to_bool(row.get("isDisabled"))
            is_listed = not is_disabled if is_disabled is not None else _to_bool(row.get("isListed"))
            market_token = _first_string(row, ("marketTokenAddress", "marketToken", "address"))
            index_token = _first_string(row, ("indexTokenAddress", "indexToken"))
            long_token = _first_string(row, ("longTokenAddress", "longToken"))
            short_token = _first_string(row, ("shortTokenAddress", "shortToken"))
            index_meta = _token_meta(token_metadata, index_token)
            long_meta = _token_meta(token_metadata, long_token)
            short_meta = _token_meta(token_metadata, short_token)
            scale_status = _scale_validation_status(token_metadata, index_meta, long_meta, short_meta)
            pool_amount_long_token = _scale_token_amount(
                raw_metrics.get("poolAmountLong"),
                long_meta.get("decimals"),
            )
            pool_amount_short_token = _scale_token_amount(
                raw_metrics.get("poolAmountShort"),
                short_meta.get("decimals"),
            )
            token_amount_scale_status = _token_amount_scale_status(
                pool_amount_long_token,
                pool_amount_short_token,
            )
            open_interest_long_usd_diagnostic = _scale_usd_amount(raw_metrics.get("openInterestLong"))
            open_interest_short_usd_diagnostic = _scale_usd_amount(raw_metrics.get("openInterestShort"))
            available_liquidity_long_usd_diagnostic = _scale_usd_amount(raw_metrics.get("availableLiquidityLong"))
            available_liquidity_short_usd_diagnostic = _scale_usd_amount(raw_metrics.get("availableLiquidityShort"))
            diagnostic_usd_scale_status = _diagnostic_usd_scale_status(
                open_interest_long_usd_diagnostic,
                open_interest_short_usd_diagnostic,
                available_liquidity_long_usd_diagnostic,
                available_liquidity_short_usd_diagnostic,
            )
            rate_relation_diagnostics = _rate_relation_diagnostics(raw_metrics)
            rate_semantics_status = _rate_semantics_status(rate_relation_diagnostics)
            rate_source_fields_diagnostic = _rate_source_fields_diagnostic(row)

            markets.append(
                {
                    "symbol": symbol,
                    "market": name,
                    "venue_id": "gmx",
                    "venue_name": "GMX",
                    "dex": "arbitrum",
                    "status": "partial",
                    "provider_status": "disabled" if is_disabled else "listed" if is_listed else "unknown",
                    "normalization_status": "raw_fixed_point",
                    "mark_price": None,
                    "mid_price": None,
                    "oracle_price": None,
                    "prev_day_price": None,
                    "funding_rate": None,
                    "funding_pct": None,
                    "open_interest_base": None,
                    "open_interest_usd": None,
                    "volume_24h_usd": None,
                    "volume_24h_base": None,
                    "premium": None,
                    "premium_pct": None,
                    "impact_bid_price": None,
                    "impact_ask_price": None,
                    "only_isolated": False,
                    "max_leverage": None,
                    "sz_decimals": None,
                    "market_token": market_token,
                    "index_token": index_token,
                    "long_token": long_token,
                    "short_token": short_token,
                    "index_token_symbol": index_meta.get("symbol"),
                    "index_token_decimals": index_meta.get("decimals"),
                    "index_token_synthetic": index_meta.get("synthetic"),
                    "long_token_symbol": long_meta.get("symbol"),
                    "long_token_decimals": long_meta.get("decimals"),
                    "long_token_synthetic": long_meta.get("synthetic"),
                    "short_token_symbol": short_meta.get("symbol"),
                    "short_token_decimals": short_meta.get("decimals"),
                    "short_token_synthetic": short_meta.get("synthetic"),
                    "scale_validation_status": scale_status,
                    "scale_validation_reason": _scale_validation_reason(scale_status),
                    "pool_amount_long_token": pool_amount_long_token,
                    "pool_amount_short_token": pool_amount_short_token,
                    "token_amount_scale_status": token_amount_scale_status,
                    "token_amount_scale_reason": _token_amount_scale_reason(token_amount_scale_status),
                    "open_interest_long_usd_diagnostic": open_interest_long_usd_diagnostic,
                    "open_interest_short_usd_diagnostic": open_interest_short_usd_diagnostic,
                    "available_liquidity_long_usd_diagnostic": available_liquidity_long_usd_diagnostic,
                    "available_liquidity_short_usd_diagnostic": available_liquidity_short_usd_diagnostic,
                    "diagnostic_usd_scale_status": diagnostic_usd_scale_status,
                    "diagnostic_usd_scale_reason": _diagnostic_usd_scale_reason(diagnostic_usd_scale_status),
                    "diagnostic_usd_scale_decimals": GMX_USD_DECIMALS,
                    "diagnostic_usd_scale_source": "gmx_interface_market_ticker_usd_decimals",
                    "rate_semantics_status": rate_semantics_status,
                    "rate_semantics_reason": _rate_semantics_reason(rate_semantics_status),
                    "rate_semantics_period": GMX_RATE_PERIOD,
                    "rate_semantics_source": GMX_RATE_SEMANTICS_SOURCE,
                    "rate_relation_diagnostics": rate_relation_diagnostics,
                    "rate_relation_summary": _rate_relation_summary_for_diagnostics(rate_relation_diagnostics),
                    "rate_source_fields_status": rate_source_fields_diagnostic["status"],
                    "rate_source_fields_diagnostic": rate_source_fields_diagnostic,
                    "is_listed": is_listed,
                    "listing_date": _string_or_none(row.get("listingDate")),
                    "raw_open_interest_long": raw_metrics.get("openInterestLong"),
                    "raw_open_interest_short": raw_metrics.get("openInterestShort"),
                    "raw_available_liquidity_long": raw_metrics.get("availableLiquidityLong"),
                    "raw_available_liquidity_short": raw_metrics.get("availableLiquidityShort"),
                    "raw_pool_amount_long": raw_metrics.get("poolAmountLong"),
                    "raw_pool_amount_short": raw_metrics.get("poolAmountShort"),
                    "raw_funding_rate_long": raw_metrics.get("fundingRateLong"),
                    "raw_funding_rate_short": raw_metrics.get("fundingRateShort"),
                    "raw_borrowing_rate_long": raw_metrics.get("borrowingRateLong"),
                    "raw_borrowing_rate_short": raw_metrics.get("borrowingRateShort"),
                    "raw_net_rate_long": raw_metrics.get("netRateLong"),
                    "raw_net_rate_short": raw_metrics.get("netRateShort"),
                    "raw_metrics": raw_metrics,
                    "resolution_action": "confirm_gmx_fixed_point_scales_and_token_decimals_before_using_liquidity_or_oi",
                    "resolution_reason": (
                        "GMX /markets/info returns fixed-point/token-unit metrics; "
                        "DeltaGrid v0 scales poolAmountLong/Short to token units only."
                    ),
                    "fetched_at": fetched_at,
                }
            )

        markets.sort(key=lambda item: (item["symbol"], item["market"]))
        return {
            "venue_id": "gmx",
            "venue_name": "GMX",
            "source": "gmx_markets_info",
            "status": "partial" if markets else "empty",
            "dex": "arbitrum",
            "requested_symbols": list(symbols),
            "markets": markets,
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "normalization_status": "raw_fixed_point" if markets else "empty",
            "scale_validation_status": _snapshot_scale_validation_status(markets, token_metadata),
            "token_amount_scale_status": _snapshot_token_amount_scale_status(markets),
            "diagnostic_usd_scale_status": _snapshot_diagnostic_usd_scale_status(markets),
            "rate_semantics_status": _snapshot_rate_semantics_status(markets),
            "rate_relation_summary": _rate_relation_summary(markets),
            "rate_source_fields_status": _snapshot_rate_source_fields_status(markets),
            "rate_source_fields_summary": _rate_source_fields_summary(markets),
            "token_metadata_source": "gmx_tokens" if token_metadata else None,
            "reason": "raw_fixed_point_metrics_require_scale_validation" if markets else "no_requested_markets",
        }

    @staticmethod
    def _empty_snapshot(symbols: tuple[str, ...], fetched_at: str, reason: str) -> dict[str, Any]:
        return {
            "venue_id": "gmx",
            "venue_name": "GMX",
            "source": "gmx_markets_info",
            "status": "empty",
            "dex": "arbitrum",
            "requested_symbols": list(symbols),
            "markets": [],
            "fetched_at": fetched_at,
            "read_only": True,
            "execution_enabled": False,
            "normalization_status": "empty",
            "scale_validation_status": "empty",
            "token_amount_scale_status": "empty",
            "diagnostic_usd_scale_status": "empty",
            "rate_semantics_status": "empty",
            "rate_relation_summary": {
                "market_count": 0,
                "side_count": 0,
                "status_counts": {},
                "source_relation_match_side_count": 0,
                "raw_sum_relation_match_side_count": 0,
                "nonzero_borrowing_side_count": 0,
                "zero_borrowing_side_count": 0,
                "zero_borrowing_ambiguous_side_count": 0,
            },
            "rate_source_fields_status": "empty",
            "rate_source_fields_summary": {
                "market_count": 0,
                "status_counts": {},
                "required_fields": list(GMX_RATE_SOURCE_FIELDS),
                "missing_fields": list(GMX_RATE_SOURCE_FIELDS),
            },
            "token_metadata_source": None,
            "reason": reason,
        }


def _market_symbol(row: dict[str, Any]) -> str:
    name = _string_or_none(row.get("name"))
    if name:
        return _canonical_symbol(name.split("[", 1)[0].strip())

    for key in ("symbol", "indexTokenSymbol", "ticker"):
        value = _string_or_none(row.get(key))
        if value:
            return _canonical_symbol(value)

    return "UNKNOWN"


def _canonical_symbol(value: str) -> str:
    normalized = value.strip().upper()
    for separator in ("/", "-"):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0]
            break
    for suffix in ("USD", "USDT", "PERP"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized


def _first_string(row: dict[str, Any], keys: tuple[str, ...]) -> Optional[str]:
    for key in keys:
        value = _string_or_none(row.get(key))
        if value:
            return value
    return None


def _token_metadata_by_address(payload: Any) -> dict[str, dict[str, Any]]:
    tokens = payload.get("tokens") if isinstance(payload, dict) else None
    if not isinstance(tokens, list):
        return {}

    metadata: dict[str, dict[str, Any]] = {}
    for token in tokens:
        if not isinstance(token, dict):
            continue
        address = _string_or_none(token.get("address"))
        decimals = _to_int(token.get("decimals"))
        if not address or decimals is None:
            continue
        metadata[address.lower()] = {
            "symbol": _string_or_none(token.get("symbol")),
            "address": address,
            "decimals": decimals,
            "synthetic": bool(token.get("synthetic")) if "synthetic" in token else False,
        }
    return metadata


def _token_meta(metadata: dict[str, dict[str, Any]], address: Optional[str]) -> dict[str, Any]:
    if not address:
        return {}
    return metadata.get(address.lower(), {})


def _scale_validation_status(
    metadata: dict[str, dict[str, Any]],
    index_meta: dict[str, Any],
    long_meta: dict[str, Any],
    short_meta: dict[str, Any],
) -> str:
    if not metadata:
        return "token_metadata_unavailable"

    required_decimals = (
        index_meta.get("decimals"),
        long_meta.get("decimals"),
        short_meta.get("decimals"),
    )
    return "token_decimals_resolved" if all(value is not None for value in required_decimals) else "token_metadata_partial"


def _scale_validation_reason(status: str) -> str:
    if status == "token_decimals_resolved":
        return "GMX token metadata resolved index/long/short token decimals; pool token amounts can be scaled, but fixed-point USD metrics still require formula validation."
    if status == "token_metadata_partial":
        return "GMX token metadata is missing one or more index/long/short token decimals."
    return "GMX token metadata was not available; fixed-point metrics remain raw only."


def _snapshot_scale_validation_status(markets: list[dict[str, Any]], metadata: dict[str, dict[str, Any]]) -> str:
    if not markets:
        return "empty"
    if not metadata:
        return "token_metadata_unavailable"
    statuses = {str(market.get("scale_validation_status")) for market in markets}
    return "token_decimals_resolved" if statuses == {"token_decimals_resolved"} else "token_metadata_partial"


def _scale_token_amount(raw_value: Optional[str], decimals: Any) -> Optional[str]:
    decimals_int = _to_int(decimals)
    if raw_value is None or decimals_int is None:
        return None

    try:
        value = Decimal(str(raw_value)) / (Decimal(10) ** decimals_int)
    except (InvalidOperation, ValueError, TypeError):
        return None

    return _decimal_to_plain_string(value)


def _scale_usd_amount(raw_value: Optional[str]) -> Optional[str]:
    if raw_value is None:
        return None

    try:
        value = Decimal(str(raw_value)) / (Decimal(10) ** GMX_USD_DECIMALS)
    except (InvalidOperation, ValueError, TypeError):
        return None

    return _decimal_to_plain_string(value)


def _decimal_to_plain_string(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _token_amount_scale_status(pool_amount_long_token: Optional[str], pool_amount_short_token: Optional[str]) -> str:
    if pool_amount_long_token is not None and pool_amount_short_token is not None:
        return "pool_amounts_scaled"
    if pool_amount_long_token is not None or pool_amount_short_token is not None:
        return "pool_amounts_partial"
    return "pool_amounts_unavailable"


def _token_amount_scale_reason(status: str) -> str:
    if status == "pool_amounts_scaled":
        return "GMX poolAmountLong/Short were scaled to token units using long/short token decimals."
    if status == "pool_amounts_partial":
        return "Only one GMX pool amount could be scaled to token units."
    return "GMX pool token amounts could not be scaled because raw values or token decimals were unavailable."


def _diagnostic_usd_scale_status(*values: Optional[str]) -> str:
    scaled_count = sum(value is not None for value in values)
    if scaled_count == len(values):
        return "usd_diagnostics_scaled"
    if scaled_count > 0:
        return "usd_diagnostics_partial"
    return "usd_diagnostics_unavailable"


def _diagnostic_usd_scale_reason(status: str) -> str:
    if status == "usd_diagnostics_scaled":
        return "GMX open interest and available liquidity fields were scaled from 1e30 USD decimals for diagnostics only."
    if status == "usd_diagnostics_partial":
        return "Only part of the GMX open interest or available liquidity fields could be scaled for diagnostics."
    return "GMX open interest and available liquidity diagnostics could not be scaled because raw values were unavailable."


def _snapshot_token_amount_scale_status(markets: list[dict[str, Any]]) -> str:
    if not markets:
        return "empty"
    statuses = {str(market.get("token_amount_scale_status")) for market in markets}
    if statuses == {"pool_amounts_scaled"}:
        return "pool_amounts_scaled"
    if "pool_amounts_scaled" in statuses or "pool_amounts_partial" in statuses:
        return "pool_amounts_partial"
    return "pool_amounts_unavailable"


def _snapshot_diagnostic_usd_scale_status(markets: list[dict[str, Any]]) -> str:
    if not markets:
        return "empty"
    statuses = {str(market.get("diagnostic_usd_scale_status")) for market in markets}
    if statuses == {"usd_diagnostics_scaled"}:
        return "usd_diagnostics_scaled"
    if "usd_diagnostics_scaled" in statuses or "usd_diagnostics_partial" in statuses:
        return "usd_diagnostics_partial"
    return "usd_diagnostics_unavailable"


def _rate_relation_diagnostics(raw_metrics: dict[str, Optional[str]]) -> dict[str, dict[str, Any]]:
    diagnostics: dict[str, dict[str, Any]] = {}
    for side, (funding_field, borrowing_field, net_field) in GMX_RATE_RELATIONS.items():
        funding_raw = raw_metrics.get(funding_field)
        borrowing_raw = raw_metrics.get(borrowing_field)
        net_raw = raw_metrics.get(net_field)
        diagnostics[side] = _rate_relation_side_diagnostic(
            funding_field,
            borrowing_field,
            net_field,
            funding_raw,
            borrowing_raw,
            net_raw,
        )
    return diagnostics


def _rate_relation_side_diagnostic(
    funding_field: str,
    borrowing_field: str,
    net_field: str,
    funding_raw: Optional[str],
    borrowing_raw: Optional[str],
    net_raw: Optional[str],
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "funding_field": funding_field,
        "borrowing_field": borrowing_field,
        "net_field": net_field,
        "status": "rate_fields_partial",
        "period": GMX_RATE_PERIOD,
        "source": GMX_RATE_SEMANTICS_SOURCE,
    }

    if funding_raw is None and borrowing_raw is None and net_raw is None:
        diagnostic["status"] = "rate_fields_unavailable"
        return diagnostic
    if funding_raw is None or borrowing_raw is None or net_raw is None:
        return diagnostic

    funding = _to_int(funding_raw)
    borrowing = _to_int(borrowing_raw)
    net = _to_int(net_raw)
    if funding is None or borrowing is None or net is None:
        diagnostic["status"] = "rate_fields_invalid"
        return diagnostic

    source_expected_net = funding - borrowing
    source_delta = net - source_expected_net
    raw_sum_expected_net = funding + borrowing
    raw_sum_delta = net - raw_sum_expected_net
    source_relation_matches = source_delta == 0
    raw_sum_relation_matches = raw_sum_delta == 0
    borrowing_is_zero = borrowing == 0
    diagnostic["source_expected_net"] = str(source_expected_net)
    diagnostic["source_delta"] = str(source_delta)
    diagnostic["raw_sum_expected_net"] = str(raw_sum_expected_net)
    diagnostic["raw_sum_delta"] = str(raw_sum_delta)
    diagnostic["source_relation_matches"] = source_relation_matches
    diagnostic["raw_sum_relation_matches"] = raw_sum_relation_matches
    diagnostic["borrowing_is_zero"] = borrowing_is_zero
    diagnostic["zero_borrowing_relation_ambiguous"] = (
        borrowing_is_zero and source_relation_matches and raw_sum_relation_matches
    )
    if diagnostic["zero_borrowing_relation_ambiguous"]:
        diagnostic["status"] = GMX_RATE_STATUS_ZERO_BORROWING
    elif source_relation_matches:
        diagnostic["status"] = GMX_RATE_STATUS_MINUS
    elif raw_sum_relation_matches:
        diagnostic["status"] = GMX_RATE_STATUS_PLUS
    else:
        diagnostic["status"] = "net_relation_mismatch"
    return diagnostic


def _rate_semantics_status(diagnostics: dict[str, dict[str, Any]]) -> str:
    statuses = {str(item.get("status")) for item in diagnostics.values()}
    return _rate_semantics_status_from_side_statuses(statuses)


def _rate_semantics_status_from_side_statuses(statuses: set[str]) -> str:
    if not statuses:
        return "rate_fields_unavailable"
    if statuses == {GMX_RATE_STATUS_MINUS}:
        return "hourly_rate_relation_confirmed"
    if statuses == {GMX_RATE_STATUS_ZERO_BORROWING}:
        return "zero_borrowing_relation_ambiguous"
    if statuses <= {GMX_RATE_STATUS_MINUS, GMX_RATE_STATUS_ZERO_BORROWING}:
        return "hourly_rate_relation_confirmed_with_zero_borrowing"
    if statuses <= {GMX_RATE_STATUS_PLUS, GMX_RATE_STATUS_ZERO_BORROWING}:
        return "raw_rate_relation_plus_with_zero_borrowing"
    if statuses <= {GMX_RATE_STATUS_MINUS, GMX_RATE_STATUS_PLUS, GMX_RATE_STATUS_ZERO_BORROWING}:
        return "raw_rate_relation_mixed"
    if "net_relation_mismatch" in statuses or "rate_fields_invalid" in statuses:
        return "hourly_rate_relation_mismatch"
    if GMX_RATE_STATUS_MINUS in statuses or GMX_RATE_STATUS_ZERO_BORROWING in statuses:
        return "hourly_rate_relation_partial"
    return "rate_fields_unavailable"


def _rate_semantics_reason(status: str) -> str:
    if status == "hourly_rate_relation_confirmed":
        return "GMX raw rate fields satisfy netRate = fundingRate - borrowingRate for long and short hourly ticker semantics; values remain raw diagnostics only."
    if status == "hourly_rate_relation_confirmed_with_zero_borrowing":
        return "GMX nonzero-borrowing sides satisfy netRate = fundingRate - borrowingRate, while zero-borrowing sides are relation-ambiguous; values remain raw diagnostics only."
    if status == "zero_borrowing_relation_ambiguous":
        return "GMX raw rate fields have zero borrowing, so funding-borrowing and funding+borrowing relations are indistinguishable; keep carry conversion blocked."
    if status == "hourly_rate_relation_partial":
        return "Only part of the GMX raw rate fields could be checked against netRate = fundingRate - borrowingRate."
    if status == "raw_rate_relation_plus_with_zero_borrowing":
        return "GMX nonzero-borrowing sides match funding+borrowing, while zero-borrowing sides are ambiguous; keep carry conversion blocked until live /markets/info mapping is reviewed."
    if status == "raw_rate_relation_mixed":
        return "GMX raw rate fields match source subtraction for some sides and funding+borrowing for others; keep carry conversion blocked until live /markets/info mapping is reviewed."
    if status == "hourly_rate_relation_mismatch":
        return "GMX raw rate fields did not satisfy the expected MarketTicker netRate relation; keep carry conversion blocked."
    return "GMX raw rate fields were unavailable or incomplete; keep carry conversion blocked."


def _snapshot_rate_semantics_status(markets: list[dict[str, Any]]) -> str:
    if not markets:
        return "empty"
    side_statuses = {
        str(diagnostic.get("status"))
        for market in markets
        for diagnostic in dict(market.get("rate_relation_diagnostics") or {}).values()
    }
    return _rate_semantics_status_from_side_statuses(side_statuses)


def _rate_relation_summary(markets: list[dict[str, Any]]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "market_count": len(markets),
        "side_count": 0,
        "status_counts": {},
        "source_relation_match_side_count": 0,
        "raw_sum_relation_match_side_count": 0,
        "nonzero_borrowing_side_count": 0,
        "zero_borrowing_side_count": 0,
        "zero_borrowing_ambiguous_side_count": 0,
    }

    status_counts: dict[str, int] = {}
    for market in markets:
        diagnostics = market.get("rate_relation_diagnostics")
        if not isinstance(diagnostics, dict):
            continue
        for diagnostic in diagnostics.values():
            if not isinstance(diagnostic, dict):
                continue
            summary["side_count"] += 1
            status = str(diagnostic.get("status") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            if diagnostic.get("source_relation_matches") is True:
                summary["source_relation_match_side_count"] += 1
            if diagnostic.get("raw_sum_relation_matches") is True:
                summary["raw_sum_relation_match_side_count"] += 1
            if diagnostic.get("borrowing_is_zero") is True:
                summary["zero_borrowing_side_count"] += 1
            elif diagnostic.get("borrowing_is_zero") is False:
                summary["nonzero_borrowing_side_count"] += 1
            if diagnostic.get("zero_borrowing_relation_ambiguous") is True:
                summary["zero_borrowing_ambiguous_side_count"] += 1

    summary["status_counts"] = dict(sorted(status_counts.items()))
    return summary


def _rate_relation_summary_for_diagnostics(diagnostics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return _rate_relation_summary([{"rate_relation_diagnostics": diagnostics}])


def _rate_source_fields_diagnostic(row: dict[str, Any]) -> dict[str, Any]:
    present_fields = [
        field for field in GMX_RATE_SOURCE_FIELDS if row.get(field) not in (None, "")
    ]
    missing_fields = [
        field for field in GMX_RATE_SOURCE_FIELDS if field not in present_fields
    ]
    if not missing_fields:
        status = "source_factor_fields_available"
    elif present_fields:
        status = "source_factor_fields_partial"
    else:
        status = "source_factor_fields_unavailable"

    return {
        "status": status,
        "required_fields": list(GMX_RATE_SOURCE_FIELDS),
        "present_fields": present_fields,
        "missing_fields": missing_fields,
        "reason": _rate_source_fields_reason(status),
        "safe_use": "source mapping diagnostics only; do not convert raw rates into carry cost",
    }


def _rate_source_fields_reason(status: str) -> str:
    if status == "source_factor_fields_available":
        return "GMX /markets/info exposes helper input fields required to recompute hourly funding and borrowing factors."
    if status == "source_factor_fields_partial":
        return "GMX /markets/info exposes only part of the helper input fields required to recompute hourly funding and borrowing factors."
    return "GMX /markets/info exposes ticker rate outputs but not helper inputs like fundingFactorPerSecond, side borrowing factors or longsPayShorts."


def _snapshot_rate_source_fields_status(markets: list[dict[str, Any]]) -> str:
    if not markets:
        return "empty"
    statuses = {str(market.get("rate_source_fields_status")) for market in markets}
    if statuses == {"source_factor_fields_available"}:
        return "source_factor_fields_available"
    if "source_factor_fields_available" in statuses or "source_factor_fields_partial" in statuses:
        return "source_factor_fields_partial"
    return "source_factor_fields_unavailable"


def _rate_source_fields_summary(markets: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    missing_fields: set[str] = set()
    present_fields: set[str] = set()
    for market in markets:
        diagnostic = market.get("rate_source_fields_diagnostic")
        if not isinstance(diagnostic, dict):
            continue
        status = str(diagnostic.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        for field in diagnostic.get("missing_fields") or []:
            missing_fields.add(str(field))
        for field in diagnostic.get("present_fields") or []:
            present_fields.add(str(field))

    return {
        "market_count": len(markets),
        "status_counts": dict(sorted(status_counts.items())),
        "required_fields": list(GMX_RATE_SOURCE_FIELDS),
        "present_fields": sorted(present_fields),
        "missing_fields": sorted(missing_fields),
    }


def _string_or_none(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, (dict, list)):
        return None
    return str(value)


def _to_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return None


def _to_int(value: Any) -> Optional[int]:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
