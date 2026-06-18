from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.common import ApiResponse
from app.services.providers.aster_client import AsterClient
from app.services.providers.coinglass_client import (
    COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES,
    DEFAULT_PERP_DEX_EXCHANGES as DEFAULT_COINGLASS_PERP_DEX_EXCHANGES,
    CoinGlassClient,
)
from app.services.providers.dydx_client import DydxClient
from app.services.providers.gmx_client import GmxClient
from app.services.providers.hyperliquid_client import HyperliquidClient
from app.services.providers.lighter_client import LighterClient

router = APIRouter(prefix="/perp-dex", tags=["perp-dex"])

DEFAULT_HYPERLIQUID_SYMBOLS = ("BTC", "ETH", "SOL")
DEFAULT_DYDX_SYMBOLS = ("BTC", "ETH", "SOL")
DEFAULT_GMX_SYMBOLS = ("BTC", "ETH", "SOL")
DEFAULT_LIGHTER_SYMBOLS = ("BTC", "ETH", "SOL")
DEFAULT_ASTER_SYMBOLS = ("BTC", "ETH", "SOL")
DEFAULT_COINGLASS_SYMBOLS = ("BTC", "ETH", "SOL")
DIRECT_VENUE_DEPTH_FRESHNESS_MAX_AGE_MS = 60_000
DIRECT_VENUE_PROVIDER_ERROR_CLASSES = {
    "timeout",
    "rate_limit",
    "empty_response",
    "schema_drift",
    "unavailable_endpoint",
    "provider_unavailable",
    "provider_http_error",
}
DIRECT_VENUE_SCHEMA_DRIFT_REASONS = {
    "unexpected_payload",
    "missing_universe",
    "missing_markets",
    "missing_order_books",
    "missing_exchange_info",
}

PERP_DEX_ROUTE_CONSTRAINTS = {
    "status": "research_only",
    "read_only": True,
    "execution_enabled": False,
    "production_liquidity_signal": False,
    "normalized_snapshot_venues": ["hyperliquid", "dydx", "lighter", "aster"],
    "raw_snapshot_venues": ["gmx"],
    "coinglass_enrichment_venues": list(DEFAULT_COINGLASS_PERP_DEX_EXCHANGES),
    "lighter_direct_snapshot": {
        "status": "direct_read_only",
        "read_only": True,
        "source": "Lighter public API",
        "source_urls": [
            "https://apidocs.lighter.xyz/docs/get-started",
            "https://apidocs.lighter.xyz/reference/orderbookdetails",
            "https://apidocs.lighter.xyz/reference/orderbookorders",
            "https://apidocs.lighter.xyz/reference/funding-rates",
            "https://docs.lighter.xyz/trading/funding",
        ],
        "confirmed_for_display": [
            "orderBooks metadata",
            "orderBookDetails market details",
            "orderBookOrders top resting orders",
            "funding-rates endpoint",
            "hourly funding concept from Lighter docs",
        ],
        "cost_input_semantics": {
            "status": "diagnostic_metadata_only",
            "fee_inputs": {
                "status": "partial_ready",
                "source_fields": ["maker_fee", "taker_fee"],
                "safe_use": "display sourced public fee fields only; do not estimate account-level route fees yet",
                "blocked_by": ["account_fee_tier", "maker_taker_side", "order_intent"],
            },
            "depth_inputs": {
                "status": "partial_ready_top_orders_only",
                "source_fields": [
                    "orderBookOrders.bids",
                    "orderBookOrders.asks",
                    "best_bid_price",
                    "best_ask_price",
                    "top_of_book_spread_bps",
                    "bid_depth_top_orders_usd",
                    "ask_depth_top_orders_usd",
                ],
                "safe_use": "display top resting order depth only; do not estimate slippage until order size, aggregation policy and liquidity caps are explicit",
                "blocked_by": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap"],
            },
            "slippage_inputs": {
                "status": "not_modeled",
                "safe_use": "do not infer slippage from display price or 24h volume",
                "blocked_by": ["orderbook_depth_or_impact_model"],
            },
            "carry_inputs": {
                "status": "input_required",
                "source_fields": ["funding_rate"],
                "safe_use": "display funding only; no holding-period carry estimate",
                "blocked_by": ["holding_period_hours", "rate_sign_convention", "position_notional_usd"],
            },
        },
        "safe_use": "direct public market context only; do not route, rank liquidity or submit orders",
        "blocked_for_production_signal": [
            "route-level liquidity ranking",
            "slippage/depth curve",
            "carry-cost conversion",
            "execution venue selection",
        ],
        "next_action": "add sourced orderbook depth/impact semantics before using Lighter in route-level scoring",
    },
    "aster_direct_snapshot": {
        "status": "direct_read_only",
        "read_only": True,
        "source": "Aster public Futures API",
        "source_urls": [
            "https://docs.asterdex.com/for-developers/aster-api/api-documentation",
            "https://docs.asterdex.com/trading/perpetuals/fees-and-specs/fees",
            "https://asterdex.github.io/aster-api-website/futures/general-info/",
            "https://asterdex.github.io/aster-api-website/futures/market-data/",
            "https://github.com/asterdex/api-docs/blob/master/V3%28Recommended%29/EN/aster-finance-futures-api-v3.md#order-book",
        ],
        "confirmed_for_display": [
            "exchangeInfo perpetual market metadata",
            "premiumIndex mark/index/funding snapshot",
            "ticker/24hr volume and rolling price context",
            "openInterest base amount snapshot",
            "ticker/bookTicker top-of-book snapshot",
            "depth order book top levels",
        ],
        "cost_input_semantics": {
            "status": "diagnostic_metadata_only",
            "fee_inputs": {
                "status": "partial_ready_published_defaults_only",
                "source_fields": ["published_usdt_perp_maker_fee", "published_usdt_perp_taker_fee"],
                "published_values": {
                    "product_scope": "USDT-Perpetual Contracts",
                    "maker_fee_bps": 0.0,
                    "taker_fee_bps": 4.0,
                    "source": "Aster Perpetual Futures Fees",
                },
                "safe_use": "published default fee metadata only; do not estimate account-level route fees until product mode, account tier and order intent are explicit",
                "blocked_by": ["account_fee_tier", "maker_taker_side", "order_intent", "fee_discount_policy"],
            },
            "depth_inputs": {
                "status": "partial_ready_depth_ladder_display_only",
                "source_fields": [
                    "fapi/v3/depth.bids",
                    "fapi/v3/depth.asks",
                    "best_bid_price",
                    "best_ask_price",
                    "top_of_book_spread_bps",
                    "bid_depth_top_orders_usd",
                    "ask_depth_top_orders_usd",
                ],
                "safe_use": "display public depth top levels only; do not estimate slippage until order size, aggregation policy, liquidity caps and stale-depth handling are explicit",
                "blocked_by": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap", "stale_depth_policy"],
            },
            "slippage_inputs": {
                "status": "not_modeled",
                "safe_use": "do not infer slippage from top-of-book or 24h volume",
                "blocked_by": ["orderbook_depth_or_impact_model"],
            },
            "carry_inputs": {
                "status": "input_required",
                "source_fields": ["funding_rate"],
                "safe_use": "display funding only; no holding-period carry estimate",
                "blocked_by": ["holding_period_hours", "rate_sign_convention", "position_notional_usd"],
            },
        },
        "safe_use": "direct public market context only; do not route, rank liquidity or submit orders",
        "blocked_for_production_signal": [
            "route-level liquidity ranking",
            "fee tier assumptions",
            "slippage/depth curve",
            "carry-cost conversion",
            "execution venue selection",
        ],
        "next_action": "source Aster fee schedule and depth/slippage semantics before using Aster in route-level scoring",
    },
    "coinglass_perp_dex_enrichment": {
        "status": "research_enrichment",
        "read_only": True,
        "source": "CoinGlass futures coins-markets",
        "source_urls": [
            "https://docs.coinglass.com/reference/futures-supported-exchanges",
            "https://docs.coinglass.com/reference/futures-coins-markets",
            "https://github.com/coinglass-official/coinglass-api-skills/blob/main/futures/trading-market/API.md",
        ],
        "default_screening_venues": list(DEFAULT_COINGLASS_PERP_DEX_EXCHANGES),
        "candidate_venues": list(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES),
        "safe_use": "third-party venue research enrichment only; do not route, rank liquidity or submit orders from these rows",
        "blocked_for_production_signal": [
            "route-level liquidity ranking",
            "execution venue selection",
            "slippage model",
            "fee model",
            "historical persistence",
        ],
        "next_action": "validate CoinGlass supported pairs/fields per candidate venue before deciding which direct adapter to add next",
    },
    "gmx_formula_validation": {
        "status": "diagnostic_only",
        "source_urls": [
            "https://github.com/gmx-io/gmx-synthetics/blob/main/contracts/utils/Precision.sol",
            "https://github.com/gmx-io/gmx-synthetics/blob/main/contracts/market/MarketUtils.sol",
            "https://github.com/gmx-io/gmx-synthetics/blob/main/contracts/reader/ReaderUtils.sol",
            "https://docs.gmx.io/docs/category/oracle-api/",
        ],
        "confirmed_for_diagnostics": [
            {
                "field_group": "poolAmountLong/poolAmountShort",
                "status": "token_amount_units",
                "scale": "token decimals from GMX /tokens",
                "safe_use": "diagnostic token-unit display only",
            },
            {
                "field_group": "Precision factors",
                "status": "float_precision_confirmed",
                "scale": "1e30",
                "safe_use": "formula inputs only; not a blanket scale for all GMX /markets/info fields",
            },
            {
                "field_group": "openInterest vs openInterestInTokens",
                "status": "separate_contract_paths_confirmed",
                "scale": "USD open interest and token open interest are separate contract getters",
                "safe_use": "raw-only until /markets/info fields are mapped to exact reader outputs",
            },
            {
                "field_group": "openInterest*/availableLiquidity*",
                "status": "gmx_api_ticker_usd_decimals_confirmed",
                "scale": "1e30 USD decimals in GMX interface MarketTicker fields",
                "safe_use": "diagnostic USD display only; do not map to normalized open_interest_usd or liquidity ranking",
            },
            {
                "field_group": "fundingRate*/borrowingRate*/netRate*",
                "status": "gmx_market_ticker_hourly_rate_semantics_guardrail_added",
                "scale": "1h factor values in GMX interface MarketTicker; source relation is netRate = fundingRate - borrowingRate, while live /markets/info needs side-aware mapping",
                "safe_use": "metadata and guardrail only; do not convert raw fields into carry cost until live nonzero-borrowing mapping and sign fixtures are added",
            },
        ],
        "blocked_for_production_signal": [
            "openInterestLong",
            "openInterestShort",
            "availableLiquidityLong",
            "availableLiquidityShort",
            "fundingRateLong",
            "fundingRateShort",
            "borrowingRateLong",
            "borrowingRateShort",
            "netRateLong",
            "netRateShort",
        ],
        "next_action": (
            "map GMX /markets/info JSON fields to exact reader/contract getters, add fixtures with expected "
            "Decimal conversions, then expose converted values as diagnostic-only before any liquidity ranking"
        ),
    },
    "capabilities": [
        {
            "id": "direct_market_snapshots",
            "label": "Direct market snapshots",
            "status": "partial_ready",
            "scope": "Hyperliquid, dYdX, Lighter and Aster normalized snapshots; GMX raw snapshot",
            "allowed": True,
            "next_action": "keep venue rows separated by normalization status",
        },
        {
            "id": "coinglass_perp_dex_enrichment",
            "label": "CoinGlass Perp DEX enrichment",
            "status": "partial_ready",
            "scope": "CoinGlass futures coin-market snapshots for DEX-like venues; research-only third-party aggregate rows. Live smoke selected Lighter/Aster as current coverage hints.",
            "allowed": True,
            "next_action": "keep CoinGlass rows as research hints after adding direct Lighter/Aster read-only snapshots",
        },
        {
            "id": "gmx_token_decimals_diagnostics",
            "label": "GMX token decimals diagnostics",
            "status": "partial_ready",
            "scope": "GMX index/long/short token metadata can be resolved from /tokens",
            "allowed": True,
            "next_action": "validate fixed-point formulas before converting raw GMX liquidity/OI metrics",
        },
        {
            "id": "gmx_pool_token_amount_diagnostics",
            "label": "GMX pool token amount diagnostics",
            "status": "partial_ready",
            "scope": "GMX poolAmountLong/Short can be scaled to token units when long/short token decimals are resolved",
            "allowed": True,
            "next_action": "keep USD liquidity/OI blocked until GMX fixed-point formulas are validated",
        },
        {
            "id": "gmx_oi_liquidity_usd_diagnostics",
            "label": "GMX OI/liquidity USD diagnostics",
            "status": "partial_ready",
            "scope": "GMX openInterest* and availableLiquidity* can be scaled from 1e30 USD decimals for diagnostics only",
            "allowed": True,
            "next_action": "keep normalized liquidity ranking blocked until route-level costs and exact field semantics are validated",
        },
        {
            "id": "route_cost_model_v0",
            "label": "Route cost model v0",
            "status": "partial_ready",
            "scope": "read-only input checklist and formula skeleton; no numeric venue cost estimates yet",
            "allowed": True,
            "next_action": "keep Lighter/Aster source semantics diagnostic-only until order intent, depth curve and carry horizon are available",
        },
        {
            "id": "lighter_aster_cost_semantics_metadata",
            "label": "Lighter/Aster cost semantics metadata",
            "status": "partial_ready",
            "scope": "Lighter exposes public maker/taker fee fields and top resting order diagnostics; Aster exposes top-of-book fields; neither has a route-ready slippage/carry model",
            "allowed": True,
            "next_action": "add sourced depth ladders or impact models and account fee tier policy before diagnostic cost bps",
        },
        {
            "id": "lighter_orderbook_orders_depth_diagnostics",
            "label": "Lighter orderBookOrders depth diagnostics",
            "status": "partial_ready",
            "scope": "Lighter orderBookOrders exposes top resting bids/asks with price and remaining base amount; safe for display-only top-order depth diagnostics",
            "allowed": True,
            "next_action": "add order-size-aware aggregation, liquidity caps and slippage math before using depth in route scoring",
        },
        {
            "id": "aster_depth_ladder_diagnostics",
            "label": "Aster depth ladder diagnostics",
            "status": "partial_ready",
            "scope": "Aster public /fapi/v3/depth exposes top bids/asks with price and base size; safe for display-only depth diagnostics",
            "allowed": True,
            "next_action": "add order-size-aware aggregation, liquidity caps and slippage math before using Aster depth in route scoring",
        },
        {
            "id": "aster_fee_schedule_metadata",
            "label": "Aster fee schedule metadata",
            "status": "partial_ready",
            "scope": "Aster published default USDT perpetual maker/taker fee rates can be shown as metadata, but not as account-level route cost",
            "allowed": True,
            "next_action": "confirm account tier, fee discount policy and order intent before using Aster fee bps in route-cost diagnostics",
        },
        {
            "id": "gmx_rate_semantics_metadata",
            "label": "GMX rate semantics metadata",
            "status": "partial_ready",
            "scope": "official source review plus offline guardrail for expected hourly ticker netRate relation; no carry conversion yet",
            "allowed": True,
            "next_action": "add side-aware sign fixtures, carry horizon and notional inputs before diagnostic carry bps",
        },
        {
            "id": "gmx_rate_relation_fixtures",
            "label": "GMX rate relation fixtures",
            "status": "partial_ready",
            "scope": "offline guardrails verify the expected source relation and the observed live-shape relation summary; live /markets/info nonzero-borrowing mapping still needs review",
            "allowed": True,
            "next_action": "map live /markets/info rate semantics and expand side-aware fixtures before numeric carry conversion",
        },
        {
            "id": "multi_venue_liquidity_ranking",
            "label": "Multi-venue liquidity ranking",
            "status": "blocked",
            "scope": "GMX pool token amounts are diagnostic only; fixed-point liquidity/OI formulas are not validated yet",
            "allowed": False,
            "next_action": "confirm GMX fixed-point scales before using raw metrics in rankings",
        },
        {
            "id": "route_level_pricing",
            "label": "Route-level pricing",
            "status": "blocked",
            "scope": "fees, slippage, price impact and borrow/funding costs are not modeled",
            "allowed": False,
            "next_action": "define per-venue fee/slippage inputs before ranking routes",
        },
        {
            "id": "execution",
            "label": "Execution",
            "status": "blocked",
            "scope": "read-only research path",
            "allowed": False,
            "next_action": "wire risk checks and explicit execution opt-in before live orders",
        },
    ],
    "blockers": [
        {
            "id": "gmx_scale_validation_required",
            "severity": "blocker",
            "scope": "gmx",
            "reason": "GMX markets/info returns fixed-point/token-unit fields; token decimals and pool token amount diagnostics are available, but raw USD liquidity/OI formulas are not validated.",
            "missing_inputs": ["exact_reader_field_mapping", "side_aware_scale_fixtures", "liquidity_formula_validation"],
            "blocked_by": ["raw_fixed_point_fields", "ambiguous_rate_mapping", "diagnostic_only_usd_scale"],
            "safe_use": "display GMX raw/token/USD diagnostics only; do not use them for liquidity ranking",
            "next_action": "validate field scales before using GMX liquidity/OI in rankings",
        },
        {
            "id": "fees_slippage_model_missing",
            "severity": "blocker",
            "scope": "all_venues",
            "reason": "Route-level cost model exists only as an input checklist; Lighter/Aster expose some sourced display fields, but complete fee tier, depth, slippage, carry and order-intent inputs are not available as numeric route-cost inputs.",
            "missing_inputs": [
                "account_fee_tier",
                "order_size_usd",
                "side",
                "depth_aggregation_policy",
                "liquidity_cap",
                "slippage_math",
                "carry_horizon",
            ],
            "blocked_by": ["display_only_depth", "metadata_only_fees", "carry_sign_convention_missing"],
            "safe_use": "show component readiness only; do not sum total cost bps or rank routes",
            "next_action": "add explicit per-venue cost inputs and order intent before production route scoring",
        },
        {
            "id": "coinglass_enrichment_not_route_input",
            "severity": "blocker",
            "scope": "coinglass_perp_dex",
            "reason": "CoinGlass futures coin-market rows are third-party aggregate enrichment and are not direct venue depth, fee or execution inputs.",
            "missing_inputs": ["direct_venue_depth", "direct_venue_fee_schedule", "execution_boundary"],
            "blocked_by": ["third_party_aggregate_rows", "no_direct_orderbook", "no_account_fee_context"],
            "safe_use": "use CoinGlass Perp DEX rows as research coverage hints only",
            "next_action": "validate direct venue adapters and pair support before using a venue in route scoring",
        },
        {
            "id": "execution_boundary",
            "severity": "blocker",
            "scope": "all_venues",
            "reason": "Current Perp DEX adapters are public read-only data clients.",
            "missing_inputs": ["connector_write_path", "risk_checks", "explicit_user_confirmation", "live_order_permission"],
            "blocked_by": ["read_only_public_clients", "no_order_submission_path", "no_route_risk_gate"],
            "safe_use": "keep all Perp DEX venue data read-only",
            "next_action": "keep execution disabled until connector, risk and confirmation flows are wired",
        },
    ],
    "ui_policy": {
        "may_show_market_rows": True,
        "may_show_research_candidates": True,
        "may_rank_by_liquidity": False,
        "may_submit_orders": False,
    },
}

PERP_DEX_ROUTE_MODEL = {
    "version": "v0",
    "status": "inputs_required",
    "read_only": True,
    "execution_enabled": False,
    "ranking_enabled": False,
    "production_signal_enabled": False,
    "model_scope": "route-level fees/slippage/routing checklist for research UI only",
    "supported_venues": ["hyperliquid", "dydx", "lighter", "aster", "gmx"],
    "third_party_enrichment_sources": ["coinglass_futures_coins_markets"],
    "model_components": [
        {
            "id": "price_source",
            "label": "Price source",
            "status": "partial_ready",
            "required_inputs": ["mark_price", "mid_price", "oracle_price", "timestamp"],
            "blocked_reason": "Venue snapshots expose prices, but route entry/exit price selection is not normalized across venues.",
        },
        {
            "id": "trading_fee",
            "label": "Trading fee",
            "status": "input_required",
            "required_inputs": ["venue_fee_schedule", "maker_taker_side", "account_fee_tier"],
            "blocked_reason": "Lighter exposes public maker/taker fee fields for display, but route-level fees still need venue-wide fee schedules, account tier policy, order side and order intent.",
        },
        {
            "id": "slippage_price_impact",
            "label": "Slippage and price impact",
            "status": "input_required",
            "required_inputs": ["order_size_usd", "side", "orderbook_depth_or_impact_model", "liquidity_cap"],
            "blocked_reason": "Current adapters do not expose a shared depth/impact model suitable for route ranking.",
        },
        {
            "id": "funding_borrow_carry",
            "label": "Funding and borrow carry",
            "status": "input_required",
            "required_inputs": ["funding_rate", "borrow_rate", "holding_period_hours", "rate_sign_convention"],
            "blocked_reason": "GMX hourly ticker source relation has an offline guardrail, but live /markets/info nonzero-borrowing sides currently match funding+borrowing while zero-borrowing sides are ambiguous; carry horizon, notional and side-aware sign fixtures are not finalized.",
        },
        {
            "id": "execution_boundary",
            "label": "Execution boundary",
            "status": "blocked",
            "required_inputs": ["connector_readiness", "risk_limits", "user_confirmation", "kill_switch"],
            "blocked_reason": "Perp DEX adapters are public read-only clients; live order path is disabled.",
        },
    ],
    "venue_readiness": [
        {
            "venue_id": "hyperliquid",
            "venue_name": "Hyperliquid",
            "status": "partial_ready",
            "available_inputs": [
                "mark_price",
                "mid_price",
                "oracle_price",
                "funding_rate",
                "open_interest_usd",
                "impact_bid_price",
                "impact_ask_price",
            ],
            "missing_inputs": ["fee_tier", "order_size", "side", "depth_curve", "carry_horizon", "execution_boundary"],
            "safe_use": "display venue market context only; do not rank routes by cost",
        },
        {
            "venue_id": "dydx",
            "venue_name": "dYdX",
            "status": "partial_ready",
            "available_inputs": [
                "oracle_price",
                "funding_rate",
                "open_interest_usd",
                "volume_24h_usd",
                "margin_fraction",
                "tick_size",
                "step_size",
            ],
            "missing_inputs": ["fee_tier", "order_size", "side", "depth_curve", "carry_horizon", "execution_boundary"],
            "safe_use": "display venue market context only; do not rank routes by cost",
        },
        {
            "venue_id": "lighter",
            "venue_name": "Lighter",
            "status": "partial_ready",
            "source_semantics": "Lighter fee fields and top resting order depth are sourced for display; slippage/carry remain metadata-only and cannot produce route-cost bps.",
            "available_inputs": [
                "last_trade_price",
                "funding_rate",
                "open_interest_usd",
                "volume_24h_usd",
                "trades_24h",
                "maker_fee",
                "taker_fee",
                "best_bid_price",
                "best_ask_price",
                "top_of_book_spread_bps",
                "bid_depth_top_orders_usd",
                "ask_depth_top_orders_usd",
                "margin_fraction",
                "tick_size",
                "step_size",
            ],
            "missing_inputs": ["order_size", "side", "depth_aggregation_policy", "liquidity_cap", "carry_horizon", "execution_boundary"],
            "cost_input_status": {
                "fees": "partial_ready_display_only",
                "depth": "partial_ready_top_orders_only",
                "slippage": "not_modeled",
                "carry": "input_required",
            },
            "safe_use": "display direct public market context only; do not rank routes by cost",
        },
        {
            "venue_id": "aster",
            "venue_name": "Aster",
            "status": "partial_ready",
            "source_semantics": "Aster top-of-book, public depth ladder and market metadata are sourced for display; fee schedule and slippage model are not route-ready.",
            "available_inputs": [
                "mark_price",
                "mid_price",
                "index_price",
                "funding_rate",
                "open_interest_usd",
                "volume_24h_usd",
                "top_of_book",
                "top_of_book_spread_bps",
                "best_bid_price",
                "best_ask_price",
                "bid_depth_top_orders_usd",
                "ask_depth_top_orders_usd",
                "published_usdt_perp_fee_schedule",
                "tick_size",
                "step_size",
                "min_notional",
            ],
            "missing_inputs": ["account_fee_tier", "order_size", "side", "depth_aggregation_policy", "liquidity_cap", "carry_horizon", "execution_boundary"],
            "cost_input_status": {
                "fees": "partial_ready_published_defaults_only",
                "depth": "partial_ready_depth_ladder_display_only",
                "slippage": "not_modeled",
                "carry": "input_required",
            },
            "safe_use": "display direct public market context only; do not rank routes by cost",
        },
        {
            "venue_id": "gmx",
            "venue_name": "GMX",
            "status": "diagnostic_only",
            "available_inputs": [
                "pool_amount_token_diagnostic",
                "open_interest_usd_diagnostic",
                "available_liquidity_usd_diagnostic",
                "hourly_rate_semantics_metadata",
            ],
            "missing_inputs": [
                "fee_schedule",
                "price_impact_formula",
                "trade_side",
                "order_size",
                "funding_borrow_rate_semantics",
                "execution_boundary",
            ],
            "safe_use": "display diagnostics only; do not convert into production liquidity ranking",
        },
        {
            "venue_id": "coinglass_perp_dex",
            "venue_name": "CoinGlass Perp DEX enrichment",
            "status": "research_enrichment",
            "available_inputs": [
                "coin_market_price",
                "funding_snapshot",
                "open_interest_snapshot",
                "optional_long_short_and_liquidation_fields",
            ],
            "missing_inputs": [
                "direct_orderbook_depth",
                "venue_fee_schedule",
                "execution_connector",
                "pair-level direct adapter validation",
                "historical persistence",
            ],
            "safe_use": "display candidate venue context only; do not rank routes or liquidity from CoinGlass aggregate rows",
        },
    ],
    "gmx_rate_semantics": {
        "status": "guardrail_metadata_only",
        "source_urls": [
            "https://github.com/gmx-io/gmx-interface/blob/master/sdk/src/utils/markets/types.ts",
            "https://github.com/gmx-io/gmx-interface/blob/master/sdk/src/utils/markets/utils.ts",
            "https://github.com/gmx-io/gmx-interface/blob/master/sdk/src/utils/fees/index.ts",
            "https://github.com/gmx-io/gmx-interface/blob/master/sdk/src/utils/numbers/utils.ts",
            "https://github.com/gmx-io/gmx-synthetics/blob/main/contracts/reader/ReaderUtils.sol",
        ],
        "confirmed_for_modeling": [
            {
                "field_group": "MarketTicker rates",
                "status": "fields_present",
                "evidence": "MarketTicker exposes fundingRateLong/Short, borrowingRateLong/Short and netRateLong/Short.",
                "safe_use": "schema metadata only",
            },
            {
                "field_group": "ticker period",
                "status": "hourly_period_confirmed",
                "evidence": "getMarketTicker computes rates using periodToSeconds(1, '1h').",
                "safe_use": "hourly label only; do not annualize or convert to carry cost yet",
            },
            {
                "field_group": "net rate relation",
                "status": "source_relation_guardrail_added",
                "evidence": "GMX interface computes netRateLong = fundingRateLong - borrowingRateLong and netRateShort = fundingRateShort - borrowingRateShort; offline guardrail verifies this expected relation for a controlled raw-field sample, while live /markets/info nonzero-borrowing fields still need mapping review.",
                "safe_use": "relationship metadata only",
            },
            {
                "field_group": "funding sign convention",
                "status": "requires_fixture_mapping",
                "evidence": "getFundingFactorPerPeriod returns negative values for the paying side and positive values for the receiving side based on longsPayShorts.",
                "safe_use": "do not interpret raw /markets/info sign until fixtures map fields to helper output",
            },
            {
                "field_group": "borrowing fee relation",
                "status": "requires_position_context",
                "evidence": "getBorrowingFactorPerPeriod multiplies side-specific borrowingFactorPerSecond by period, and getBorrowingFeeRateUsd applies the factor to sizeInUsd.",
                "safe_use": "requires order size and holding period before carry cost",
            },
        ],
        "mapping_review": {
            "status": "source_vs_live_mapping_unresolved",
            "source_confirmed": [
                "MarketTicker exposes fundingRateLong/Short, borrowingRateLong/Short and netRateLong/Short",
                "getMarketTicker computes hourly rates with periodToSeconds(1, '1h')",
                "GMX interface computes netRateLong/Short as fundingRateLong/Short - borrowingRateLong/Short",
            ],
            "source_inputs_required": [
                "fundingFactorPerSecond",
                "borrowingFactorPerSecondForLongs",
                "borrowingFactorPerSecondForShorts",
                "longsPayShorts",
            ],
            "live_observed": [
                "BTC/ETH/SOL /markets/info sample: nonzero-borrowing sides matched fundingRate + borrowingRate",
                "zero-borrowing sides are relation-ambiguous and must not be counted as source-relation confirmation",
                "current /markets/info payload does not expose helper inputs required to recompute MarketTicker hourly rates",
            ],
            "diagnostic_fields": [
                "rate_semantics_status",
                "rate_relation_diagnostics",
                "rate_relation_summary",
                "rate_source_fields_status",
                "rate_source_fields_summary",
            ],
            "safe_use": "mapping evidence only; no percent, bps, annualized or carry-cost conversion",
        },
        "blocked_for_numeric_carry": [
            "live /markets/info source helper inputs unavailable",
            "live /markets/info nonzero borrowing rate mapping review",
            "broader live fixture coverage across market states",
            "side-aware funding sign tests",
            "holding_period_hours input",
            "position_notional_usd input",
            "production decision on hourly vs annualized display",
        ],
        "fixture_coverage": [
            {
                "id": "net_rate_relation_raw_fields",
                "status": "offline_guardrail_added",
                "scope": "raw fundingRateLong/Short, borrowingRateLong/Short and netRateLong/Short strings",
                "assertion": "netRate = fundingRate - borrowingRate for long and short sides",
                "safe_use": "relation diagnostic only; no percent, bps, annualized or carry-cost conversion",
            },
            {
                "id": "live_nonzero_borrowing_raw_sum_relation_observed",
                "status": "live_smoke_observed",
                "scope": "live GMX /markets/info BTC/ETH/SOL sample",
                "assertion": "nonzero-borrowing sides match netRate = fundingRate + borrowingRate in the observed sample",
                "safe_use": "block carry conversion until raw field mapping is reconciled with interface helper semantics",
            },
            {
                "id": "live_zero_borrowing_relation_ambiguity",
                "status": "live_smoke_observed",
                "scope": "live GMX /markets/info BTC/ETH/SOL sample",
                "assertion": "zero-borrowing sides cannot distinguish funding-borrowing from funding+borrowing because both relations produce the same raw netRate",
                "safe_use": "do not count zero-borrowing matches as source-relation confirmation",
            },
            {
                "id": "live_shape_offline_fixture",
                "status": "offline_guardrail_added",
                "scope": "backend/tests/fixtures/gmx_rate_live_shape_fixture.json",
                "assertion": "one nonzero-borrowing side matches funding+borrowing and one zero-borrowing side remains ambiguous",
                "safe_use": "fixture coverage for diagnostic status and summary only",
            }
        ],
        "next_action": "map live GMX /markets/info nonzero-borrowing rate semantics, then add side-aware fixtures and sourced fee/depth/carry inputs before exposing diagnostic carry bps",
    },
    "required_inputs": [
        {
            "id": "venue_fee_schedule",
            "label": "Venue fee schedule",
            "reason": "Maker/taker fee and account tier must be explicit before estimated route costs are shown.",
        },
        {
            "id": "order_intent",
            "label": "Order intent",
            "reason": "Side, notional, size unit and reduce-only/opening intent affect fee, slippage and risk.",
        },
        {
            "id": "depth_or_impact_model",
            "label": "Depth or impact model",
            "reason": "Slippage and price impact require orderbook depth or venue-specific impact formulas.",
        },
        {
            "id": "carry_horizon",
            "label": "Carry horizon",
            "reason": "Funding and borrow costs need a holding period and rate sign convention.",
        },
        {
            "id": "risk_limits",
            "label": "Risk limits",
            "reason": "Route allowance must honor max notional, leverage, liquidation buffer and kill-switch state.",
        },
    ],
    "formula_skeleton": {
        "gross_edge_bps": "expected_exit_price_bps - expected_entry_price_bps",
        "estimated_cost_bps": "trading_fee_bps + slippage_bps + price_impact_bps + funding_borrow_carry_bps",
        "net_edge_bps": "gross_edge_bps - estimated_cost_bps",
        "route_allowed": "net_edge_bps > threshold_bps and liquidity_cap_ok and execution_boundary_ok",
    },
    "diagnostic_cost_estimate_v0": {
        "status": "blocked_for_numeric_total",
        "read_only": True,
        "may_emit_numeric_total_bps": False,
        "safe_use": "show component readiness only; do not sum venue cost or rank routes",
        "components": [
            {
                "id": "lighter_fee_fields",
                "label": "Lighter maker/taker fee fields",
                "venue_id": "lighter",
                "status": "source_fields_available_unit_unconfirmed",
                "source_fields": ["maker_fee", "taker_fee"],
                "may_emit_component_bps": False,
                "required_input_ids": ["venue_fee_schedule", "order_intent"],
                "blocked_by": ["fee unit confirmation", "account fee tier", "maker_taker_side", "order_intent"],
                "safe_use": "display raw public fee fields only",
            },
            {
                "id": "lighter_top_order_depth",
                "label": "Lighter top resting order depth",
                "venue_id": "lighter",
                "status": "partial_ready_display_only",
                "source_fields": [
                    "best_bid_price",
                    "best_ask_price",
                    "top_of_book_spread_bps",
                    "bid_depth_top_orders_usd",
                    "ask_depth_top_orders_usd",
                ],
                "may_emit_component_bps": True,
                "required_input_ids": ["order_intent", "depth_or_impact_model"],
                "blocked_by": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap", "slippage_math"],
                "safe_use": "display top-of-book spread and top-order depth only; do not treat as executable slippage",
            },
            {
                "id": "aster_published_fee_schedule",
                "label": "Aster published USDT perpetual fee schedule",
                "venue_id": "aster",
                "status": "partial_ready_published_defaults_only",
                "source_fields": ["published_usdt_perp_maker_fee", "published_usdt_perp_taker_fee"],
                "published_values": {
                    "maker_fee_bps": 0.0,
                    "taker_fee_bps": 4.0,
                    "product_scope": "USDT-Perpetual Contracts",
                },
                "may_emit_component_bps": False,
                "required_input_ids": ["venue_fee_schedule", "order_intent"],
                "blocked_by": ["account fee tier", "fee discount policy", "maker_taker_side", "order_intent"],
                "safe_use": "published fee metadata only; not execution-grade account fee",
            },
            {
                "id": "aster_top_of_book_spread",
                "label": "Aster top-of-book spread",
                "venue_id": "aster",
                "status": "partial_ready_display_only",
                "source_fields": ["bid_price", "ask_price", "mid_price", "top_of_book_spread_bps"],
                "may_emit_component_bps": True,
                "required_input_ids": ["order_intent", "depth_or_impact_model"],
                "blocked_by": ["depth curve", "order size", "side", "liquidity cap"],
                "safe_use": "display spread only; do not treat as slippage or executable depth",
            },
            {
                "id": "aster_depth_ladder",
                "label": "Aster depth ladder",
                "venue_id": "aster",
                "status": "partial_ready_display_only",
                "source_fields": [
                    "best_bid_price",
                    "best_ask_price",
                    "top_of_book_spread_bps",
                    "bid_depth_top_orders_usd",
                    "ask_depth_top_orders_usd",
                ],
                "may_emit_component_bps": True,
                "required_input_ids": ["order_intent", "depth_or_impact_model"],
                "blocked_by": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap", "slippage_math"],
                "safe_use": "display Aster public depth ladder only; do not treat as executable slippage",
            },
            {
                "id": "slippage_price_impact",
                "label": "Slippage and price impact",
                "venue_id": "all",
                "status": "input_required",
                "source_fields": [],
                "may_emit_component_bps": False,
                "required_input_ids": ["order_intent", "depth_or_impact_model"],
                "blocked_by": ["orderbook depth ladder or venue impact model", "order_size_usd", "side"],
                "safe_use": "blocked until source-backed depth/impact model exists",
            },
            {
                "id": "funding_borrow_carry",
                "label": "Funding and borrow carry",
                "venue_id": "all",
                "status": "input_required",
                "source_fields": ["funding_rate"],
                "may_emit_component_bps": False,
                "required_input_ids": ["order_intent", "carry_horizon"],
                "blocked_by": ["holding_period_hours", "rate sign convention", "position_notional_usd"],
                "safe_use": "display funding only; do not estimate holding-period carry",
            },
        ],
        "next_action": "wire route-cost diagnostics only for components with confirmed units, explicit order intent and source-backed depth/carry inputs",
    },
    "output_policy": {
        "may_show_checklist": True,
        "may_show_formula_skeleton": True,
        "may_show_diagnostic_cost_components": True,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
    },
    "blockers": [
        {
            "id": "numeric_fee_inputs_missing",
            "severity": "blocker",
            "reason": "Sourced public maker/taker fee fields are available only for Lighter display; route-level fees still need complete venue schedules, account tiers and order-side intent.",
            "missing_inputs": ["venue_fee_schedule", "account_fee_tier", "maker_taker_side", "order_intent"],
            "blocked_by": ["display_fee_fields_only", "published_defaults_not_account_fee"],
            "safe_use": "show fee metadata only; do not calculate account-level fee bps",
        },
        {
            "id": "slippage_impact_inputs_missing",
            "severity": "blocker",
            "reason": "No shared orderbook depth or price impact model is available across venues.",
            "missing_inputs": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap", "slippage_math"],
            "blocked_by": ["display_only_depth", "no_order_size_context", "no_stale_depth_policy"],
            "safe_use": "show top-of-book/depth diagnostics only; do not estimate executable slippage",
        },
        {
            "id": "gmx_rate_semantics_pending",
            "severity": "blocker",
            "reason": "GMX funding/borrowing/net rate semantics are not normalized into carry cost.",
            "missing_inputs": ["rate_sign_convention", "side_aware_rate_fixtures", "holding_period_hours", "position_notional_usd"],
            "blocked_by": ["source_vs_live_mapping_unresolved", "helper_inputs_unavailable"],
            "safe_use": "show GMX rate relation diagnostics only; do not estimate carry bps",
        },
        {
            "id": "coinglass_enrichment_not_route_input",
            "severity": "blocker",
            "reason": "CoinGlass Perp DEX rows are third-party coin-level aggregates, not direct route-level depth/fee/execution inputs.",
            "missing_inputs": ["direct_venue_adapter", "direct_orderbook_depth", "direct_fee_schedule"],
            "blocked_by": ["third_party_aggregate_rows", "no_execution_context"],
            "safe_use": "use CoinGlass rows as research enrichment only",
        },
        {
            "id": "execution_boundary",
            "severity": "blocker",
            "reason": "Perp DEX route model is read-only and cannot submit orders.",
            "missing_inputs": ["connector_write_path", "risk_checks", "explicit_user_confirmation"],
            "blocked_by": ["read_only_route_model", "no_order_submission_path"],
            "safe_use": "keep route model read-only",
        },
    ],
    "next_action": "source fee/depth/carry inputs per venue, then add diagnostic numeric cost estimates without enabling ranking or execution",
}


def _build_diagnostic_cost_summary(
    diagnostics: dict,
    required_inputs: list[dict] | None = None,
    gmx_rate_semantics: dict | None = None,
) -> dict:
    components = diagnostics.get("components")
    components = components if isinstance(components, list) else []
    required_inputs = required_inputs if isinstance(required_inputs, list) else []
    gmx_rate_semantics = gmx_rate_semantics if isinstance(gmx_rate_semantics, dict) else {}
    display_components = [item for item in components if item.get("may_emit_component_bps") is True]
    blocked_numeric_components = [item for item in components if item.get("may_emit_component_bps") is not True]
    sourced_components = [item for item in components if item.get("source_fields")]
    venue_groups: dict[str, list[dict]] = {}
    for item in components:
        venue_id = item.get("venue_id") or "unknown"
        venue_groups.setdefault(venue_id, []).append(item)
    blocker_groups: dict[str, list[dict]] = {}
    for item in components:
        blockers = item.get("blocked_by")
        blockers = blockers if isinstance(blockers, list) else []
        for blocker in blockers:
            if not blocker:
                continue
            blocker_groups.setdefault(str(blocker), []).append(item)

    venue_labels = {
        "lighter": "Lighter",
        "aster": "Aster",
        "all": "Cross-venue",
        "unknown": "Unknown",
    }
    venue_breakdown = []
    for venue_id, venue_components in venue_groups.items():
        venue_display_components = [item for item in venue_components if item.get("may_emit_component_bps") is True]
        venue_blocked_components = [item for item in venue_components if item.get("may_emit_component_bps") is not True]
        venue_sourced_components = [item for item in venue_components if item.get("source_fields")]
        venue_breakdown.append(
            {
                "venue_id": venue_id,
                "venue_label": venue_labels.get(venue_id, venue_id.replace("_", " ").title()),
                "component_count": len(venue_components),
                "display_only_component_count": len(venue_display_components),
                "blocked_numeric_component_count": len(venue_blocked_components),
                "sourced_component_count": len(venue_sourced_components),
                "component_ids": [item.get("id") for item in venue_components if item.get("id")],
                "display_component_ids": [item.get("id") for item in venue_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in venue_blocked_components if item.get("id")],
                "sourced_component_ids": [item.get("id") for item in venue_sourced_components if item.get("id")],
                "numeric_total_status": "blocked",
                "safe_use": "venue-level component readiness only; do not rank routes or estimate executable cost",
            }
        )
    blocker_breakdown = []
    for blocker, blocker_components in blocker_groups.items():
        blocker_display_components = [item for item in blocker_components if item.get("may_emit_component_bps") is True]
        blocker_blocked_components = [item for item in blocker_components if item.get("may_emit_component_bps") is not True]
        venue_ids = []
        for item in blocker_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in venue_ids:
                venue_ids.append(venue_id)
        blocker_breakdown.append(
            {
                "blocker": blocker,
                "component_count": len(blocker_components),
                "component_ids": [item.get("id") for item in blocker_components if item.get("id")],
                "venue_ids": venue_ids,
                "display_component_ids": [item.get("id") for item in blocker_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in blocker_blocked_components if item.get("id")],
                "numeric_total_status": "blocked",
                "safe_use": "blocker visibility only; source required inputs before estimating route cost",
            }
        )

    required_input_next_actions = {
        "venue_fee_schedule": "confirm venue fee units, account tier and maker/taker side before fee bps can be calculated",
        "order_intent": "define side, notional, size unit and intent before applying fee, depth or carry diagnostics",
        "depth_or_impact_model": "source order-size-aware depth aggregation, liquidity caps and slippage math before impact bps",
        "carry_horizon": "define holding period, position notional and rate sign convention before carry bps",
        "risk_limits": "define max notional, leverage, liquidation buffer and kill-switch gates before route allowance",
    }
    required_input_breakdown = []
    for required_input in required_inputs:
        input_id = required_input.get("id")
        if not input_id:
            continue
        input_components = [
            item
            for item in components
            if input_id in (item.get("required_input_ids") if isinstance(item.get("required_input_ids"), list) else [])
        ]
        input_display_components = [item for item in input_components if item.get("may_emit_component_bps") is True]
        input_blocked_components = [item for item in input_components if item.get("may_emit_component_bps") is not True]
        input_sourced_components = [item for item in input_components if item.get("source_fields")]
        venue_ids = []
        for item in input_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in venue_ids:
                venue_ids.append(venue_id)
        if not input_components:
            input_status = "route_gate_only"
        elif input_sourced_components:
            input_status = "partial_ready_display_only"
        else:
            input_status = "input_required"
        required_input_breakdown.append(
            {
                "input_id": input_id,
                "input_label": required_input.get("label") or str(input_id).replace("_", " ").title(),
                "status": input_status,
                "reason": required_input.get("reason", ""),
                "component_count": len(input_components),
                "component_ids": [item.get("id") for item in input_components if item.get("id")],
                "venue_ids": venue_ids,
                "display_component_ids": [item.get("id") for item in input_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in input_blocked_components if item.get("id")],
                "sourced_component_ids": [item.get("id") for item in input_sourced_components if item.get("id")],
                "numeric_total_status": "blocked",
                "safe_use": "required-input readiness only; do not estimate route cost or rank venues",
                "next_action": required_input_next_actions.get(input_id, "source this required input before numeric route cost"),
            }
        )

    source_field_groups: dict[str, list[dict]] = {}
    for item in components:
        source_fields = item.get("source_fields")
        source_fields = source_fields if isinstance(source_fields, list) else []
        for source_field in source_fields:
            if not source_field:
                continue
            source_field_groups.setdefault(str(source_field), []).append(item)
    source_field_breakdown = []
    for source_field, source_components in source_field_groups.items():
        field_display_components = [item for item in source_components if item.get("may_emit_component_bps") is True]
        field_blocked_components = [item for item in source_components if item.get("may_emit_component_bps") is not True]
        venue_ids = []
        required_input_ids = []
        for item in source_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in venue_ids:
                venue_ids.append(venue_id)
            for input_id in (item.get("required_input_ids") if isinstance(item.get("required_input_ids"), list) else []):
                if input_id not in required_input_ids:
                    required_input_ids.append(input_id)
        source_field_breakdown.append(
            {
                "source_field": source_field,
                "status": "display_context_only",
                "component_count": len(source_components),
                "component_ids": [item.get("id") for item in source_components if item.get("id")],
                "venue_ids": venue_ids,
                "required_input_ids": required_input_ids,
                "display_component_ids": [item.get("id") for item in field_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in field_blocked_components if item.get("id")],
                "numeric_total_status": "blocked",
                "safe_use": "source-field visibility only; do not treat sourced display fields as route-cost inputs",
            }
        )

    safe_use_groups: dict[str, list[dict]] = {}
    for item in components:
        safe_use = item.get("safe_use")
        if not safe_use:
            continue
        safe_use_groups.setdefault(str(safe_use), []).append(item)
    safe_use_breakdown = []
    for safe_use, safe_use_components in safe_use_groups.items():
        safe_use_display_components = [item for item in safe_use_components if item.get("may_emit_component_bps") is True]
        safe_use_blocked_components = [item for item in safe_use_components if item.get("may_emit_component_bps") is not True]
        venue_ids = []
        required_input_ids = []
        for item in safe_use_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in venue_ids:
                venue_ids.append(venue_id)
            for input_id in (item.get("required_input_ids") if isinstance(item.get("required_input_ids"), list) else []):
                if input_id not in required_input_ids:
                    required_input_ids.append(input_id)
        safe_use_breakdown.append(
            {
                "safe_use": safe_use,
                "status": "boundary_notice",
                "component_count": len(safe_use_components),
                "component_ids": [item.get("id") for item in safe_use_components if item.get("id")],
                "venue_ids": venue_ids,
                "required_input_ids": required_input_ids,
                "display_component_ids": [item.get("id") for item in safe_use_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in safe_use_blocked_components if item.get("id")],
                "numeric_total_status": "blocked",
                "next_action": "keep this boundary visible until required route-cost inputs are sourced and tested",
            }
        )

    rollup_definitions = [
        {
            "category_id": "fees",
            "category_label": "Fees",
            "required_input_ids": ["venue_fee_schedule", "order_intent"],
            "component_ids": ["lighter_fee_fields", "aster_published_fee_schedule"],
            "next_action": "confirm fee units, account tier and maker/taker side before fee bps",
        },
        {
            "category_id": "depth_slippage",
            "category_label": "Depth / Slippage",
            "required_input_ids": ["order_intent", "depth_or_impact_model"],
            "component_ids": [
                "lighter_top_order_depth",
                "aster_top_of_book_spread",
                "aster_depth_ladder",
                "slippage_price_impact",
            ],
            "next_action": "source order-size-aware depth aggregation, liquidity caps and stale-depth policy before slippage bps",
        },
        {
            "category_id": "carry",
            "category_label": "Carry",
            "required_input_ids": ["order_intent", "carry_horizon"],
            "component_ids": ["funding_borrow_carry"],
            "next_action": "define holding period, notional and rate sign convention before carry bps",
        },
        {
            "category_id": "risk_limits",
            "category_label": "Risk Limits",
            "required_input_ids": ["risk_limits"],
            "component_ids": [],
            "next_action": "source risk gates before route allowance or execution boundary changes",
        },
    ]
    readiness_rollup = []
    for rollup in rollup_definitions:
        rollup_required_input_ids = rollup["required_input_ids"]
        rollup_component_ids = rollup["component_ids"]
        rollup_components = [item for item in components if item.get("id") in rollup_component_ids]
        rollup_display_components = [item for item in rollup_components if item.get("may_emit_component_bps") is True]
        rollup_blocked_components = [item for item in rollup_components if item.get("may_emit_component_bps") is not True]
        rollup_sourced_components = [item for item in rollup_components if item.get("source_fields")]
        if not rollup_components:
            rollup_status = "route_gate_only"
        elif rollup_sourced_components:
            rollup_status = "partial_ready_display_only"
        else:
            rollup_status = "input_required"
        readiness_rollup.append(
            {
                "category_id": rollup["category_id"],
                "category_label": rollup["category_label"],
                "status": rollup_status,
                "required_input_ids": rollup_required_input_ids,
                "component_count": len(rollup_components),
                "sourced_component_count": len(rollup_sourced_components),
                "display_component_ids": [item.get("id") for item in rollup_display_components if item.get("id")],
                "blocked_numeric_component_ids": [item.get("id") for item in rollup_blocked_components if item.get("id")],
                "numeric_total_status": "blocked",
                "safe_use": "compact readiness only; do not rank venues, estimate route cost or submit orders",
                "next_action": rollup["next_action"],
            }
        )

    components_by_id = {item.get("id"): item for item in components if item.get("id")}
    fee_schedule_evidence_definitions = [
        {
            "evidence_id": "lighter_fee_schedule_evidence",
            "evidence_label": "Lighter Fee Schedule Evidence",
            "venue_id": "lighter",
            "venue_label": "Lighter",
            "status": "fee_policy_required",
            "source_component_id": "lighter_fee_fields",
            "source_scope": "public maker/taker fee fields",
            "required_input_ids": ["venue_fee_schedule", "order_intent"],
            "required_policy_inputs": [
                "account_fee_tier",
                "fee_unit_confirmation",
                "maker_taker_side",
                "order_side",
                "order_size_usd",
                "order_intent_type",
                "reduce_only_or_opening_intent",
            ],
            "manual_approval_ids": [
                "lighter_fee_unit_review",
                "lighter_account_fee_tier_review",
                "lighter_order_intent_fee_review",
            ],
            "blocked_by": [
                "raw_public_fee_fields_only",
                "fee_unit_unconfirmed",
                "account_fee_tier_missing",
                "order_intent_missing",
            ],
            "blocked_outputs": ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"],
            "safe_use": "Lighter fee fields are display-only until units, account tier and order intent are approved",
        },
        {
            "evidence_id": "aster_fee_schedule_evidence",
            "evidence_label": "Aster Fee Schedule Evidence",
            "venue_id": "aster",
            "venue_label": "Aster",
            "status": "fee_policy_required",
            "source_component_id": "aster_published_fee_schedule",
            "source_scope": "published USDT perpetual fee defaults",
            "required_input_ids": ["venue_fee_schedule", "order_intent"],
            "required_policy_inputs": [
                "account_fee_tier",
                "fee_schedule_source_confirmation",
                "fee_discount_policy",
                "maker_taker_side",
                "order_side",
                "order_size_usd",
                "order_intent_type",
                "reduce_only_or_opening_intent",
            ],
            "manual_approval_ids": [
                "aster_fee_schedule_source_review",
                "aster_account_fee_tier_review",
                "aster_fee_discount_policy_review",
                "aster_order_intent_fee_review",
            ],
            "blocked_by": [
                "published_defaults_not_account_fee",
                "account_fee_tier_missing",
                "fee_discount_policy_unconfirmed",
                "order_intent_missing",
            ],
            "blocked_outputs": ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"],
            "safe_use": "Aster published defaults are metadata only until account tier, discounts and order intent are approved",
        },
    ]
    fee_schedule_evidence_checklist = []
    for definition in fee_schedule_evidence_definitions:
        component = components_by_id.get(definition["source_component_id"], {})
        source_fields = component.get("source_fields") if isinstance(component.get("source_fields"), list) else []
        published_values = component.get("published_values") if isinstance(component.get("published_values"), dict) else {}
        fee_schedule_evidence_checklist.append(
            {
                "evidence_id": definition["evidence_id"],
                "evidence_label": definition["evidence_label"],
                "venue_id": definition["venue_id"],
                "venue_label": definition["venue_label"],
                "status": definition["status"],
                "source_component_id": definition["source_component_id"],
                "source_scope": definition["source_scope"],
                "source_fields": source_fields,
                "published_values": published_values,
                "required_input_ids": definition["required_input_ids"],
                "required_policy_inputs": definition["required_policy_inputs"],
                "manual_approval_ids": definition["manual_approval_ids"],
                "blocked_by": definition["blocked_by"],
                "blocked_outputs": definition["blocked_outputs"],
                "may_emit_fee_bps": False,
                "may_estimate_cost_bps": False,
                "may_rank_routes": False,
                "may_submit_orders": False,
                "numeric_total_status": "blocked",
                "safe_use": definition["safe_use"],
                "next_action": "confirm fee units, account tier and maker/taker side before fee bps",
            }
        )

    def add_unique_value(target: list[str], value: str) -> None:
        if value and value not in target:
            target.append(value)

    fee_schedule_evidence_summary = {
        "status": "fee_schedule_evidence_required",
        "evidence_count": len(fee_schedule_evidence_checklist),
        "blocked_evidence_count": len(fee_schedule_evidence_checklist),
        "venue_ids": [],
        "component_ids": [],
        "source_fields": [],
        "required_input_ids": [],
        "required_policy_inputs": [],
        "manual_approval_ids": [],
        "blocked_outputs": [],
        "may_emit_fee_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "numeric_total_status": "blocked",
        "safe_use": "fee schedule evidence only; do not emit fee bps, total route cost, ranking or execution",
        "next_action": "confirm account fee tier, fee units, discount policy and order intent before fee bps",
    }
    for evidence in fee_schedule_evidence_checklist:
        add_unique_value(fee_schedule_evidence_summary["venue_ids"], evidence["venue_id"])
        add_unique_value(fee_schedule_evidence_summary["component_ids"], evidence["source_component_id"])
        for key in (
            "source_fields",
            "required_input_ids",
            "required_policy_inputs",
            "manual_approval_ids",
            "blocked_outputs",
        ):
            for value in evidence[key]:
                add_unique_value(fee_schedule_evidence_summary[key], value)

    depth_policy_definitions = [
        {
            "policy_id": "lighter_top_order_depth_staleness",
            "venue_id": "lighter",
            "venue_label": "Lighter",
            "component_id": "lighter_top_order_depth",
            "depth_scope": "top resting orders",
            "source_endpoint": "orderBookOrders",
            "required_policy_inputs": [
                "depth_snapshot_timestamp",
                "max_depth_age_ms",
                "stale_depth_action",
                "order_size_usd",
                "side",
                "depth_aggregation_policy",
                "liquidity_cap",
            ],
            "next_action": "add timestamp freshness, stale-depth policy and order-size aggregation before Lighter slippage bps",
        },
        {
            "policy_id": "aster_top_of_book_staleness",
            "venue_id": "aster",
            "venue_label": "Aster",
            "component_id": "aster_top_of_book_spread",
            "depth_scope": "top-of-book ticker",
            "source_endpoint": "ticker/bookTicker",
            "required_policy_inputs": [
                "depth_snapshot_timestamp",
                "max_depth_age_ms",
                "stale_depth_action",
                "order_size_usd",
                "side",
                "depth_aggregation_policy",
                "liquidity_cap",
            ],
            "next_action": "add freshness policy and depth-source precedence before Aster top-of-book can inform slippage",
        },
        {
            "policy_id": "aster_depth_ladder_staleness",
            "venue_id": "aster",
            "venue_label": "Aster",
            "component_id": "aster_depth_ladder",
            "depth_scope": "public depth ladder",
            "source_endpoint": "fapi/v3/depth",
            "required_policy_inputs": [
                "depth_snapshot_timestamp",
                "max_depth_age_ms",
                "stale_depth_action",
                "order_size_usd",
                "side",
                "depth_aggregation_policy",
                "liquidity_cap",
            ],
            "next_action": "add timestamp freshness, stale-depth policy and order-size ladder aggregation before Aster slippage bps",
        },
    ]
    depth_staleness_policy_checklist = []
    for policy in depth_policy_definitions:
        component = components_by_id.get(policy["component_id"], {})
        depth_staleness_policy_checklist.append(
            {
                "policy_id": policy["policy_id"],
                "venue_id": policy["venue_id"],
                "venue_label": policy["venue_label"],
                "component_id": policy["component_id"],
                "depth_scope": policy["depth_scope"],
                "source_endpoint": policy["source_endpoint"],
                "status": "staleness_policy_required",
                "source_fields": component.get("source_fields") if isinstance(component.get("source_fields"), list) else [],
                "required_policy_inputs": policy["required_policy_inputs"],
                "blocked_by": ["no_depth_snapshot_timestamp", "no_max_depth_age_ms", "no_stale_depth_action", "no_order_size_context"],
                "may_emit_slippage_bps": False,
                "numeric_total_status": "blocked",
                "safe_use": "depth/staleness policy checklist only; do not estimate slippage, route cost or ranking",
                "next_action": policy["next_action"],
            }
        )

    policy_input_next_actions = {
        "depth_snapshot_timestamp": "source per-venue depth snapshot timestamps before freshness checks",
        "max_depth_age_ms": "define maximum allowed depth age by venue and endpoint before stale-depth handling",
        "stale_depth_action": "define whether stale depth is hidden, warned or blocks slippage diagnostics",
        "order_size_usd": "define order notional before depth aggregation can be evaluated",
        "side": "define buy/sell side before choosing bid or ask depth",
        "depth_aggregation_policy": "define order-size-aware depth aggregation before slippage diagnostics",
        "liquidity_cap": "define liquidity caps before any depth-derived route signal",
    }
    required_policy_input_breakdown = []
    policy_input_ids = depth_policy_definitions[0]["required_policy_inputs"] if depth_policy_definitions else []
    for policy_input_id in policy_input_ids:
        input_policies = [
            policy
            for policy in depth_staleness_policy_checklist
            if policy_input_id in (policy.get("required_policy_inputs") if isinstance(policy.get("required_policy_inputs"), list) else [])
        ]
        policy_ids = []
        component_ids = []
        venue_ids = []
        source_endpoints = []
        blocked_by = []
        for policy in input_policies:
            for value, target in (
                (policy.get("policy_id"), policy_ids),
                (policy.get("component_id"), component_ids),
                (policy.get("venue_id"), venue_ids),
                (policy.get("source_endpoint"), source_endpoints),
            ):
                if value and value not in target:
                    target.append(value)
            for blocker in policy.get("blocked_by") if isinstance(policy.get("blocked_by"), list) else []:
                if blocker and blocker not in blocked_by:
                    blocked_by.append(blocker)
        required_policy_input_breakdown.append(
            {
                "input_id": policy_input_id,
                "input_label": policy_input_id.replace("_", " ").title(),
                "status": "policy_input_required",
                "policy_count": len(input_policies),
                "policy_ids": policy_ids,
                "component_ids": component_ids,
                "venue_ids": venue_ids,
                "source_endpoints": source_endpoints,
                "blocked_by": blocked_by,
                "may_emit_slippage_bps": False,
                "numeric_total_status": "blocked",
                "safe_use": "policy-input readiness only; do not estimate slippage, route cost or ranking",
                "next_action": policy_input_next_actions.get(policy_input_id, "source this policy input before slippage diagnostics"),
            }
        )

    next_action_groups: dict[str, dict] = {}

    def add_next_action_source(
        *,
        next_action: str,
        source_type: str,
        source_id: str,
        required_input_ids: list[str] | None = None,
        required_policy_inputs: list[str] | None = None,
        component_ids: list[str] | None = None,
        venue_ids: list[str] | None = None,
        policy_ids: list[str] | None = None,
        rollup_category_ids: list[str] | None = None,
    ) -> None:
        if not next_action:
            return
        group = next_action_groups.setdefault(
            next_action,
            {
                "action_id": f"next_action_{len(next_action_groups) + 1}",
                "next_action": next_action,
                "status": "action_required",
                "source_count": 0,
                "source_types": [],
                "source_ids": [],
                "required_input_ids": [],
                "required_policy_inputs": [],
                "component_ids": [],
                "venue_ids": [],
                "policy_ids": [],
                "rollup_category_ids": [],
                "numeric_total_status": "blocked",
                "safe_use": "next-action planning only; do not estimate route cost, rank routes or submit orders",
            },
        )
        group["source_count"] += 1
        for value, key in (
            (source_type, "source_types"),
            (source_id, "source_ids"),
        ):
            if value and value not in group[key]:
                group[key].append(value)
        for values, key in (
            (required_input_ids or [], "required_input_ids"),
            (required_policy_inputs or [], "required_policy_inputs"),
            (component_ids or [], "component_ids"),
            (venue_ids or [], "venue_ids"),
            (policy_ids or [], "policy_ids"),
            (rollup_category_ids or [], "rollup_category_ids"),
        ):
            for value in values:
                if value and value not in group[key]:
                    group[key].append(value)

    for input_row in required_input_breakdown:
        add_next_action_source(
            next_action=input_row.get("next_action", ""),
            source_type="required_input",
            source_id=input_row.get("input_id", ""),
            required_input_ids=[input_row.get("input_id")] if input_row.get("input_id") else [],
            component_ids=input_row.get("component_ids") if isinstance(input_row.get("component_ids"), list) else [],
            venue_ids=input_row.get("venue_ids") if isinstance(input_row.get("venue_ids"), list) else [],
        )
    for rollup in readiness_rollup:
        rollup_component_ids = (
            list(rollup.get("display_component_ids"))
            if isinstance(rollup.get("display_component_ids"), list)
            else []
        )
        rollup_blocked_component_ids = (
            rollup.get("blocked_numeric_component_ids")
            if isinstance(rollup.get("blocked_numeric_component_ids"), list)
            else []
        )
        for component_id in rollup_blocked_component_ids:
            if component_id not in rollup_component_ids:
                rollup_component_ids.append(component_id)
        rollup_venue_ids = []
        for component_id in rollup_component_ids:
            venue_id = components_by_id.get(component_id, {}).get("venue_id")
            if venue_id and venue_id not in rollup_venue_ids:
                rollup_venue_ids.append(venue_id)
        add_next_action_source(
            next_action=rollup.get("next_action", ""),
            source_type="readiness_rollup",
            source_id=rollup.get("category_id", ""),
            required_input_ids=rollup.get("required_input_ids") if isinstance(rollup.get("required_input_ids"), list) else [],
            component_ids=rollup_component_ids,
            venue_ids=rollup_venue_ids,
            rollup_category_ids=[rollup.get("category_id")] if rollup.get("category_id") else [],
        )
    for policy in depth_staleness_policy_checklist:
        add_next_action_source(
            next_action=policy.get("next_action", ""),
            source_type="depth_staleness_policy",
            source_id=policy.get("policy_id", ""),
            required_policy_inputs=policy.get("required_policy_inputs") if isinstance(policy.get("required_policy_inputs"), list) else [],
            component_ids=[policy.get("component_id")] if policy.get("component_id") else [],
            venue_ids=[policy.get("venue_id")] if policy.get("venue_id") else [],
            policy_ids=[policy.get("policy_id")] if policy.get("policy_id") else [],
        )
    for evidence in fee_schedule_evidence_checklist:
        add_next_action_source(
            next_action=evidence.get("next_action", ""),
            source_type="fee_schedule_evidence",
            source_id=evidence.get("evidence_id", ""),
            required_input_ids=evidence.get("required_input_ids") if isinstance(evidence.get("required_input_ids"), list) else [],
            required_policy_inputs=evidence.get("required_policy_inputs") if isinstance(evidence.get("required_policy_inputs"), list) else [],
            component_ids=[evidence.get("source_component_id")] if evidence.get("source_component_id") else [],
            venue_ids=[evidence.get("venue_id")] if evidence.get("venue_id") else [],
        )
    next_action_breakdown = list(next_action_groups.values())

    source_input_action_coverage = []
    for index, source_row in enumerate(source_field_breakdown, start=1):
        source_component_ids = (
            source_row.get("component_ids")
            if isinstance(source_row.get("component_ids"), list)
            else []
        )
        source_required_input_ids = (
            source_row.get("required_input_ids")
            if isinstance(source_row.get("required_input_ids"), list)
            else []
        )
        matched_actions = []
        for action in next_action_breakdown:
            action_required_input_ids = (
                action.get("required_input_ids")
                if isinstance(action.get("required_input_ids"), list)
                else []
            )
            action_component_ids = (
                action.get("component_ids")
                if isinstance(action.get("component_ids"), list)
                else []
            )
            if any(input_id in action_required_input_ids for input_id in source_required_input_ids) or any(
                component_id in action_component_ids for component_id in source_component_ids
            ):
                matched_actions.append(action)

        next_action_ids = []
        next_actions = []
        source_types = []
        for action in matched_actions:
            for value, target in (
                (action.get("action_id"), next_action_ids),
                (action.get("next_action"), next_actions),
            ):
                if value and value not in target:
                    target.append(value)
            for source_type in action.get("source_types") if isinstance(action.get("source_types"), list) else []:
                if source_type and source_type not in source_types:
                    source_types.append(source_type)

        source_input_action_coverage.append(
            {
                "coverage_id": f"source_field_{index}",
                "source_field": source_row.get("source_field"),
                "status": "display_context_only",
                "component_count": source_row.get("component_count", 0),
                "component_ids": source_component_ids,
                "venue_ids": source_row.get("venue_ids") if isinstance(source_row.get("venue_ids"), list) else [],
                "required_input_count": len(source_required_input_ids),
                "required_input_ids": source_required_input_ids,
                "next_action_count": len(next_actions),
                "next_action_ids": next_action_ids,
                "next_actions": next_actions,
                "source_types": source_types,
                "display_component_ids": source_row.get("display_component_ids")
                if isinstance(source_row.get("display_component_ids"), list)
                else [],
                "blocked_numeric_component_ids": source_row.get("blocked_numeric_component_ids")
                if isinstance(source_row.get("blocked_numeric_component_ids"), list)
                else [],
                "numeric_total_status": "blocked",
                "safe_use": "source-input-action coverage only; display source fields do not close route-ready inputs or ranking",
                "next_action": "complete mapped next actions before treating this source field as route-ready input",
            }
        )

    def source_fields_for_components(component_ids: list[str]) -> list[str]:
        source_fields = []
        for source_row in source_field_breakdown:
            row_component_ids = (
                source_row.get("component_ids")
                if isinstance(source_row.get("component_ids"), list)
                else []
            )
            if not any(component_id in row_component_ids for component_id in component_ids):
                continue
            source_field = source_row.get("source_field")
            if source_field and source_field not in source_fields:
                source_fields.append(source_field)
        return source_fields

    depth_policy_ids = [
        policy.get("policy_id")
        for policy in depth_staleness_policy_checklist
        if policy.get("policy_id")
    ]
    route_ready_evidence_definitions = [
        {
            "gate_id": "fee_schedule_evidence",
            "gate_label": "Fee Schedule Evidence",
            "required_input_ids": ["venue_fee_schedule"],
            "required_policy_inputs": [],
            "component_ids": ["lighter_fee_fields", "aster_published_fee_schedule"],
            "policy_ids": [],
            "blocked_outputs": ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"],
            "next_action": "confirm account fee tier, fee units and maker/taker side before fee bps",
        },
        {
            "gate_id": "order_intent_evidence",
            "gate_label": "Order Intent Evidence",
            "required_input_ids": ["order_intent"],
            "required_policy_inputs": ["order_size_usd", "side"],
            "component_ids": [
                "lighter_fee_fields",
                "lighter_top_order_depth",
                "aster_top_of_book_spread",
                "aster_depth_ladder",
                "slippage_price_impact",
                "funding_borrow_carry",
            ],
            "policy_ids": depth_policy_ids,
            "blocked_outputs": ["fee_bps", "slippage_bps", "carry_bps", "estimated_cost_bps", "route_allowed"],
            "next_action": "define order size, side, notional and intent before route-cost evidence can be evaluated",
        },
        {
            "gate_id": "depth_freshness_evidence",
            "gate_label": "Depth Freshness Evidence",
            "required_input_ids": ["depth_or_impact_model"],
            "required_policy_inputs": ["depth_snapshot_timestamp", "max_depth_age_ms", "stale_depth_action"],
            "component_ids": ["lighter_top_order_depth", "aster_top_of_book_spread", "aster_depth_ladder"],
            "policy_ids": depth_policy_ids,
            "blocked_outputs": ["slippage_bps", "estimated_cost_bps", "route_allowed"],
            "next_action": "source depth timestamps, maximum age policy and stale-depth handling before slippage bps",
        },
        {
            "gate_id": "depth_aggregation_evidence",
            "gate_label": "Depth Aggregation Evidence",
            "required_input_ids": ["depth_or_impact_model"],
            "required_policy_inputs": ["order_size_usd", "side", "depth_aggregation_policy", "liquidity_cap"],
            "component_ids": [
                "lighter_top_order_depth",
                "aster_top_of_book_spread",
                "aster_depth_ladder",
                "slippage_price_impact",
            ],
            "policy_ids": depth_policy_ids,
            "blocked_outputs": ["slippage_bps", "estimated_cost_bps", "route_allowed"],
            "next_action": "define order-size-aware aggregation, side selection and liquidity caps before slippage bps",
        },
        {
            "gate_id": "carry_semantics_evidence",
            "gate_label": "Carry Semantics Evidence",
            "required_input_ids": ["carry_horizon"],
            "required_policy_inputs": [],
            "component_ids": ["funding_borrow_carry"],
            "policy_ids": [],
            "blocked_outputs": ["carry_bps", "estimated_cost_bps", "net_edge_bps"],
            "next_action": "define holding period, notional and funding/borrowing sign convention before carry bps",
        },
        {
            "gate_id": "risk_limits_evidence",
            "gate_label": "Risk Limits Evidence",
            "required_input_ids": ["risk_limits"],
            "required_policy_inputs": [],
            "component_ids": [],
            "policy_ids": [],
            "blocked_outputs": ["route_allowed", "may_submit_orders"],
            "next_action": "source risk gates before route allowance or execution boundary changes",
        },
    ]
    route_ready_evidence_checklist = []
    for definition in route_ready_evidence_definitions:
        component_ids = definition["component_ids"]
        source_field_ids = source_fields_for_components(component_ids)
        route_ready_evidence_checklist.append(
            {
                "gate_id": definition["gate_id"],
                "gate_label": definition["gate_label"],
                "status": "evidence_required",
                "required_input_ids": definition["required_input_ids"],
                "required_policy_inputs": definition["required_policy_inputs"],
                "component_ids": component_ids,
                "policy_ids": definition["policy_ids"],
                "source_field_ids": source_field_ids,
                "blocked_outputs": definition["blocked_outputs"],
                "evidence_count": len(source_field_ids),
                "numeric_total_status": "blocked",
                "may_estimate_cost_bps": False,
                "may_rank_routes": False,
                "may_submit_orders": False,
                "safe_use": "route-ready evidence checklist only; do not estimate route cost, rank routes or submit orders",
                "next_action": definition["next_action"],
            }
        )

    evidence_by_gate_id = {
        evidence.get("gate_id"): evidence
        for evidence in route_ready_evidence_checklist
        if evidence.get("gate_id")
    }

    def append_unique(target: list[str], values: list[str]) -> None:
        for value in values:
            if value and value not in target:
                target.append(value)

    def evidence_values(gate_ids: list[str], key: str) -> list[str]:
        values = []
        for gate_id in gate_ids:
            gate = evidence_by_gate_id.get(gate_id, {})
            gate_values = gate.get(key) if isinstance(gate.get(key), list) else []
            append_unique(values, gate_values)
        return values

    gmx_mapping_review = gmx_rate_semantics.get("mapping_review")
    gmx_mapping_review = gmx_mapping_review if isinstance(gmx_mapping_review, dict) else {}
    gmx_fixture_coverage = gmx_rate_semantics.get("fixture_coverage")
    gmx_fixture_coverage = gmx_fixture_coverage if isinstance(gmx_fixture_coverage, list) else []
    gmx_diagnostic_field_ids = (
        gmx_mapping_review.get("diagnostic_fields")
        if isinstance(gmx_mapping_review.get("diagnostic_fields"), list)
        else []
    )
    gmx_fixture_coverage_ids = [
        item.get("id")
        for item in gmx_fixture_coverage
        if isinstance(item, dict) and item.get("id")
    ]
    venue_evidence_definitions = [
        {
            "venue_id": "lighter",
            "venue_label": "Lighter",
            "venue_scope": "direct_venue",
            "status": "venue_evidence_required",
            "venue_gate_ids": [
                "fee_schedule_evidence",
                "order_intent_evidence",
                "depth_freshness_evidence",
                "depth_aggregation_evidence",
            ],
            "cross_venue_gate_ids": ["carry_semantics_evidence", "risk_limits_evidence"],
            "component_ids": ["lighter_fee_fields", "lighter_top_order_depth"],
            "policy_ids": ["lighter_top_order_depth_staleness"],
            "diagnostic_field_ids": [],
            "fixture_coverage_ids": [],
            "next_action": "source Lighter account fee tier, order intent and depth policy before route-ready Lighter costing",
        },
        {
            "venue_id": "aster",
            "venue_label": "Aster",
            "venue_scope": "direct_venue",
            "status": "venue_evidence_required",
            "venue_gate_ids": [
                "fee_schedule_evidence",
                "order_intent_evidence",
                "depth_freshness_evidence",
                "depth_aggregation_evidence",
            ],
            "cross_venue_gate_ids": ["carry_semantics_evidence", "risk_limits_evidence"],
            "component_ids": [
                "aster_published_fee_schedule",
                "aster_top_of_book_spread",
                "aster_depth_ladder",
            ],
            "policy_ids": ["aster_top_of_book_staleness", "aster_depth_ladder_staleness"],
            "diagnostic_field_ids": [],
            "fixture_coverage_ids": [],
            "next_action": "source Aster account fee tier, order intent, depth aggregation and stale-depth policy before route-ready Aster costing",
        },
        {
            "venue_id": "gmx",
            "venue_label": "GMX",
            "venue_scope": "raw_mapping_review",
            "status": "mapping_review_required",
            "venue_gate_ids": ["gmx_rate_mapping_review"],
            "cross_venue_gate_ids": ["order_intent_evidence", "carry_semantics_evidence", "risk_limits_evidence"],
            "component_ids": [],
            "policy_ids": [],
            "diagnostic_field_ids": gmx_diagnostic_field_ids,
            "fixture_coverage_ids": gmx_fixture_coverage_ids,
            "next_action": gmx_rate_semantics.get("next_action")
            or "map live GMX rate semantics before carry bps",
        },
        {
            "venue_id": "cross_venue",
            "venue_label": "Cross-venue",
            "venue_scope": "cross_venue",
            "status": "cross_venue_evidence_required",
            "venue_gate_ids": ["carry_semantics_evidence", "risk_limits_evidence"],
            "cross_venue_gate_ids": [],
            "component_ids": ["funding_borrow_carry"],
            "policy_ids": [],
            "diagnostic_field_ids": [],
            "fixture_coverage_ids": [],
            "next_action": "define carry horizon, risk limits and execution boundary before any route allowance",
        },
    ]
    venue_evidence_status = []
    for definition in venue_evidence_definitions:
        gate_ids = definition["venue_gate_ids"] + definition["cross_venue_gate_ids"]
        required_input_ids = evidence_values(gate_ids, "required_input_ids")
        required_policy_inputs = evidence_values(gate_ids, "required_policy_inputs")
        blocked_outputs = evidence_values(gate_ids, "blocked_outputs")
        source_field_ids = source_fields_for_components(definition["component_ids"])
        if definition["venue_id"] == "gmx":
            append_unique(required_input_ids, ["order_intent", "carry_horizon", "risk_limits"])
            append_unique(blocked_outputs, ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"])
        venue_evidence_status.append(
            {
                "venue_id": definition["venue_id"],
                "venue_label": definition["venue_label"],
                "venue_scope": definition["venue_scope"],
                "status": definition["status"],
                "venue_gate_ids": definition["venue_gate_ids"],
                "cross_venue_gate_ids": definition["cross_venue_gate_ids"],
                "required_input_ids": required_input_ids,
                "required_policy_inputs": required_policy_inputs,
                "component_ids": definition["component_ids"],
                "policy_ids": definition["policy_ids"],
                "source_field_ids": source_field_ids,
                "diagnostic_field_ids": definition["diagnostic_field_ids"],
                "fixture_coverage_ids": definition["fixture_coverage_ids"],
                "blocked_outputs": blocked_outputs,
                "evidence_count": len(source_field_ids)
                + len(definition["diagnostic_field_ids"])
                + len(definition["fixture_coverage_ids"]),
                "numeric_total_status": "blocked",
                "may_estimate_cost_bps": False,
                "may_rank_routes": False,
                "may_submit_orders": False,
                "safe_use": "venue evidence status only; do not estimate route cost, rank routes or submit orders",
                "next_action": definition["next_action"],
            }
        )

    may_emit_numeric_total = diagnostics.get("may_emit_numeric_total_bps") is True
    return {
        "status": diagnostics.get("status", "unavailable"),
        "boundary": "component_readiness_only",
        "component_count": len(components),
        "display_only_component_count": len(display_components),
        "blocked_numeric_component_count": len(blocked_numeric_components),
        "sourced_component_count": len(sourced_components),
        "component_ids": [item.get("id") for item in components if item.get("id")],
        "display_component_ids": [item.get("id") for item in display_components if item.get("id")],
        "blocked_numeric_component_ids": [item.get("id") for item in blocked_numeric_components if item.get("id")],
        "sourced_component_ids": [item.get("id") for item in sourced_components if item.get("id")],
        "venue_breakdown": venue_breakdown,
        "blocker_breakdown": blocker_breakdown,
        "required_input_breakdown": required_input_breakdown,
        "source_field_breakdown": source_field_breakdown,
        "safe_use_breakdown": safe_use_breakdown,
        "readiness_rollup": readiness_rollup,
        "fee_schedule_evidence_summary": fee_schedule_evidence_summary,
        "fee_schedule_evidence_checklist": fee_schedule_evidence_checklist,
        "depth_staleness_policy_checklist": depth_staleness_policy_checklist,
        "required_policy_input_breakdown": required_policy_input_breakdown,
        "next_action_breakdown": next_action_breakdown,
        "source_input_action_coverage": source_input_action_coverage,
        "route_ready_evidence_checklist": route_ready_evidence_checklist,
        "venue_evidence_status": venue_evidence_status,
        "may_emit_numeric_total_bps": may_emit_numeric_total,
        "numeric_total_status": "allowed" if may_emit_numeric_total else "blocked",
        "safe_use": diagnostics.get("safe_use", "show component readiness only"),
        "next_action": diagnostics.get("next_action", "source required cost inputs before total bps"),
    }


def _build_gmx_rate_mapping_review(gmx_rate_semantics: dict) -> dict:
    gmx_rate_semantics = gmx_rate_semantics if isinstance(gmx_rate_semantics, dict) else {}
    mapping_review = gmx_rate_semantics.get("mapping_review")
    mapping_review = mapping_review if isinstance(mapping_review, dict) else {}
    fixture_coverage = gmx_rate_semantics.get("fixture_coverage")
    fixture_coverage = fixture_coverage if isinstance(fixture_coverage, list) else []
    confirmed_for_modeling = gmx_rate_semantics.get("confirmed_for_modeling")
    confirmed_for_modeling = confirmed_for_modeling if isinstance(confirmed_for_modeling, list) else []
    blocked_for_numeric_carry = gmx_rate_semantics.get("blocked_for_numeric_carry")
    blocked_for_numeric_carry = blocked_for_numeric_carry if isinstance(blocked_for_numeric_carry, list) else []
    diagnostic_field_ids = (
        mapping_review.get("diagnostic_fields")
        if isinstance(mapping_review.get("diagnostic_fields"), list)
        else []
    )
    source_inputs_required = (
        mapping_review.get("source_inputs_required")
        if isinstance(mapping_review.get("source_inputs_required"), list)
        else []
    )
    fixture_coverage_ids = [
        item.get("id")
        for item in fixture_coverage
        if isinstance(item, dict) and item.get("id")
    ]
    source_confirmed = (
        mapping_review.get("source_confirmed")
        if isinstance(mapping_review.get("source_confirmed"), list)
        else []
    )
    live_observed = (
        mapping_review.get("live_observed")
        if isinstance(mapping_review.get("live_observed"), list)
        else []
    )
    source_relation_status = "source_relation_guardrail_added"
    for item in confirmed_for_modeling:
        if isinstance(item, dict) and item.get("field_group") == "net rate relation":
            source_relation_status = item.get("status") or source_relation_status
            break
    blocked_outputs = ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"]
    safe_use = "GMX rate mapping review only; no percent, bps, annualized or carry-cost conversion"
    side_aware_fixture_expectations = [
        {
            "expectation_id": "long_position_pays_when_longs_pay_shorts_true",
            "case_id": "longs_pay_shorts_direction",
            "case_label": "Long pays when longsPayShorts=true",
            "status": "fixture_required",
            "position_side": "long",
            "longs_pay_shorts": True,
            "expected_funding_direction": "pay",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "fixture_coverage_ids": [],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "add fixture where long side pays funding when longsPayShorts is true",
        },
        {
            "expectation_id": "short_position_receives_when_longs_pay_shorts_true",
            "case_id": "longs_pay_shorts_direction",
            "case_label": "Short receives when longsPayShorts=true",
            "status": "fixture_required",
            "position_side": "short",
            "longs_pay_shorts": True,
            "expected_funding_direction": "receive",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "fixture_coverage_ids": [],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "add fixture where short side receives funding when longsPayShorts is true",
        },
        {
            "expectation_id": "short_position_pays_when_longs_pay_shorts_false",
            "case_id": "longs_pay_shorts_direction",
            "case_label": "Short pays when longsPayShorts=false",
            "status": "fixture_required",
            "position_side": "short",
            "longs_pay_shorts": False,
            "expected_funding_direction": "pay",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "fixture_coverage_ids": [],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "add fixture where short side pays funding when longsPayShorts is false",
        },
        {
            "expectation_id": "long_position_receives_when_longs_pay_shorts_false",
            "case_id": "longs_pay_shorts_direction",
            "case_label": "Long receives when longsPayShorts=false",
            "status": "fixture_required",
            "position_side": "long",
            "longs_pay_shorts": False,
            "expected_funding_direction": "receive",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "fixture_coverage_ids": [],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "add fixture where long side receives funding when longsPayShorts is false",
        },
    ]
    side_aware_expectation_ids = [
        expectation["expectation_id"]
        for expectation in side_aware_fixture_expectations
    ]
    review_items = [
        {
            "review_id": "source_relation_guardrail",
            "review_label": "Source Relation Guardrail",
            "status": source_relation_status,
            "evidence_count": len(source_confirmed),
            "diagnostic_field_ids": ["rate_relation_summary"],
            "source_inputs_required": [],
            "fixture_coverage_ids": ["net_rate_relation_raw_fields"],
            "blocked_by": ["live /markets/info nonzero borrowing rate mapping review"],
            "blocked_outputs": blocked_outputs,
            "safe_use": safe_use,
            "next_action": "keep source relation guardrail while mapping live /markets/info fields",
        },
        {
            "review_id": "live_nonzero_borrowing_mapping",
            "review_label": "Live Nonzero Borrowing Mapping",
            "status": "mapping_review_required",
            "evidence_count": len(live_observed),
            "diagnostic_field_ids": ["rate_relation_summary", "rate_relation_diagnostics"],
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": [
                "live_nonzero_borrowing_raw_sum_relation_observed",
                "live_zero_borrowing_relation_ambiguity",
                "live_shape_offline_fixture",
            ],
            "blocked_by": [
                "live /markets/info nonzero borrowing rate mapping review",
                "broader live fixture coverage across market states",
            ],
            "blocked_outputs": blocked_outputs,
            "safe_use": safe_use,
            "next_action": "reconcile live funding+borrowing observation with source helper relation before carry bps",
        },
        {
            "review_id": "source_helper_inputs",
            "review_label": "Source Helper Inputs",
            "status": "source_inputs_missing",
            "evidence_count": 0,
            "diagnostic_field_ids": ["rate_source_fields_status", "rate_source_fields_summary"],
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": [],
            "blocked_by": ["live /markets/info source helper inputs unavailable"],
            "blocked_outputs": blocked_outputs,
            "safe_use": safe_use,
            "next_action": "source helper inputs or fixtures for fundingFactorPerSecond, borrowing factors and longsPayShorts",
        },
        {
            "review_id": "carry_conversion_boundary",
            "review_label": "Carry Conversion Boundary",
            "status": "blocked_for_carry_conversion",
            "evidence_count": len(fixture_coverage_ids),
            "diagnostic_field_ids": diagnostic_field_ids,
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": fixture_coverage_ids,
            "blocked_by": blocked_for_numeric_carry,
            "blocked_outputs": blocked_outputs,
            "safe_use": safe_use,
            "next_action": "complete mapping review, side-aware fixtures, holding period and notional before carry conversion",
        },
    ]

    def append_unique(values: list[str], value: str) -> None:
        if value and value not in values:
            values.append(value)

    def slug_id(value: str) -> str:
        chars = []
        previous_separator = False
        for char in value.lower():
            if char.isalnum():
                chars.append(char)
                previous_separator = False
            elif not previous_separator:
                chars.append("_")
                previous_separator = True
        return "".join(chars).strip("_") or "unknown"

    blocker_groups: dict[str, dict] = {}
    for review_item in review_items:
        for blocker in review_item["blocked_by"]:
            blocker_id = slug_id(blocker)
            group = blocker_groups.setdefault(
                blocker_id,
                {
                    "blocker_id": blocker_id,
                    "blocker": blocker,
                    "review_count": 0,
                    "review_ids": [],
                    "review_statuses": [],
                    "source_inputs_required": [],
                    "fixture_coverage_ids": [],
                    "blocked_outputs": [],
                    "may_emit_carry_bps": False,
                    "may_estimate_cost_bps": False,
                    "may_rank_routes": False,
                    "may_submit_orders": False,
                    "safe_use": safe_use,
                    "next_action": "clear this blocker before GMX carry conversion or route-cost diagnostics",
                },
            )
            append_unique(group["review_ids"], review_item["review_id"])
            append_unique(group["review_statuses"], review_item["status"])
            for source_input in review_item["source_inputs_required"]:
                append_unique(group["source_inputs_required"], source_input)
            for fixture_id in review_item["fixture_coverage_ids"]:
                append_unique(group["fixture_coverage_ids"], fixture_id)
            for output_id in review_item["blocked_outputs"]:
                append_unique(group["blocked_outputs"], output_id)
            group["review_count"] = len(group["review_ids"])

    fixture_by_id = {
        item.get("id"): item
        for item in fixture_coverage
        if isinstance(item, dict) and item.get("id")
    }

    def fixture_evidence_count(case_fixture_ids: list[str]) -> int:
        return len([fixture_id for fixture_id in case_fixture_ids if fixture_id in fixture_by_id])

    fixture_readiness_matrix = [
        {
            "case_id": "source_relation_raw_fields",
            "case_label": "Source Relation Raw Fields",
            "status": fixture_by_id.get("net_rate_relation_raw_fields", {}).get("status", source_relation_status),
            "evidence_count": fixture_evidence_count(["net_rate_relation_raw_fields"]),
            "diagnostic_field_ids": ["rate_relation_summary"],
            "source_inputs_required": [],
            "fixture_coverage_ids": ["net_rate_relation_raw_fields"],
            "blocked_by": ["live /markets/info nonzero borrowing rate mapping review"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "keep source relation fixture, but do not use it as live mapping confirmation",
        },
        {
            "case_id": "live_nonzero_borrowing_relation",
            "case_label": "Live Nonzero Borrowing Relation",
            "status": "mapping_review_required",
            "evidence_count": fixture_evidence_count(
                [
                    "live_nonzero_borrowing_raw_sum_relation_observed",
                    "live_shape_offline_fixture",
                ]
            ),
            "diagnostic_field_ids": ["rate_relation_summary", "rate_relation_diagnostics"],
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": [
                "live_nonzero_borrowing_raw_sum_relation_observed",
                "live_shape_offline_fixture",
            ],
            "blocked_by": [
                "live /markets/info nonzero borrowing rate mapping review",
                "broader live fixture coverage across market states",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "reconcile observed funding+borrowing relation with source helper semantics",
        },
        {
            "case_id": "live_zero_borrowing_ambiguity",
            "case_label": "Live Zero Borrowing Ambiguity",
            "status": "relation_ambiguous",
            "evidence_count": fixture_evidence_count(["live_zero_borrowing_relation_ambiguity"]),
            "diagnostic_field_ids": ["rate_relation_summary", "rate_relation_diagnostics"],
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": ["live_zero_borrowing_relation_ambiguity"],
            "blocked_by": [
                "live /markets/info nonzero borrowing rate mapping review",
                "broader live fixture coverage across market states",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "do not treat zero-borrowing matches as source relation proof",
        },
        {
            "case_id": "longs_pay_shorts_direction",
            "case_label": "longsPayShorts Direction",
            "status": "fixture_required",
            "evidence_count": 0,
            "diagnostic_field_ids": ["rate_source_fields_status", "rate_source_fields_summary"],
            "source_inputs_required": ["fundingFactorPerSecond", "longsPayShorts"],
            "fixture_coverage_ids": [],
            "expectation_ids": side_aware_expectation_ids,
            "expectation_notes": [
                "long position pays funding when longsPayShorts=true",
                "short position receives funding when longsPayShorts=true",
                "short position pays funding when longsPayShorts=false",
                "long position receives funding when longsPayShorts=false",
            ],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "add side-aware fixtures for paying/receiving direction before carry bps",
        },
        {
            "case_id": "source_helper_inputs_presence",
            "case_label": "Source Helper Inputs Presence",
            "status": "source_inputs_missing",
            "evidence_count": 0,
            "diagnostic_field_ids": ["rate_source_fields_status", "rate_source_fields_summary"],
            "source_inputs_required": source_inputs_required,
            "fixture_coverage_ids": [],
            "blocked_by": ["live /markets/info source helper inputs unavailable"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "safe_use": safe_use,
            "next_action": "source helper inputs or equivalent fixtures before GMX carry conversion",
        },
    ]
    mapping_decision_checklist = [
        {
            "check_id": "source_helper_inputs_available",
            "check_label": "Source Helper Inputs Available",
            "status": "source_inputs_missing",
            "required_source_inputs": source_inputs_required,
            "required_fixture_case_ids": ["source_helper_inputs_presence"],
            "required_expectation_ids": [],
            "required_review_ids": ["source_helper_inputs"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_source_helper_input_review",
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "confirm source helper inputs or equivalent fixtures before diagnostic carry bps",
        },
        {
            "check_id": "nonzero_borrowing_relation_reviewed",
            "check_label": "Nonzero Borrowing Relation Reviewed",
            "status": "mapping_review_required",
            "required_source_inputs": source_inputs_required,
            "required_fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
            ],
            "required_expectation_ids": [],
            "required_review_ids": ["live_nonzero_borrowing_mapping"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_live_nonzero_borrowing_mapping_review",
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "resolve live funding+borrowing observation against source helper semantics",
        },
        {
            "check_id": "side_aware_direction_fixtures",
            "check_label": "Side-aware Direction Fixtures",
            "status": "fixture_required",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "required_fixture_case_ids": ["longs_pay_shorts_direction"],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_review_ids": ["carry_conversion_boundary"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_side_aware_sign_review",
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "cover long/short paying and receiving fixtures before any carry conversion",
        },
        {
            "check_id": "carry_inputs_defined",
            "check_label": "Carry Inputs Defined",
            "status": "input_required",
            "required_source_inputs": [],
            "required_fixture_case_ids": ["source_relation_raw_fields", "longs_pay_shorts_direction"],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_review_ids": ["carry_conversion_boundary"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_carry_horizon_notional_review",
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "define holding_period_hours, position_notional_usd and sign convention before carry bps",
        },
        {
            "check_id": "display_unit_decision_recorded",
            "check_label": "Display Unit Decision Recorded",
            "status": "policy_input_required",
            "required_source_inputs": [],
            "required_fixture_case_ids": [],
            "required_expectation_ids": [],
            "required_review_ids": ["carry_conversion_boundary"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_hourly_vs_annualized_display_decision",
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record whether diagnostics display hourly or annualized units before showing any bps",
        },
    ]
    mapping_decision_manual_approval_ids = [
        check["manual_approval_id"]
        for check in mapping_decision_checklist
        if check["manual_approval_required"]
    ]
    carry_input_checklist = [
        {
            "input_id": "holding_period_hours",
            "input_label": "Holding Period Hours",
            "status": "input_required",
            "input_type": "runtime_input",
            "required_source_inputs": [],
            "required_fixture_case_ids": [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": ["carry_inputs_defined"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_carry_horizon_notional_review",
            "blocked_by": ["holding_period_hours input"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "define holding_period_hours before diagnostic GMX carry bps",
        },
        {
            "input_id": "position_notional_usd",
            "input_label": "Position Notional USD",
            "status": "input_required",
            "input_type": "runtime_input",
            "required_source_inputs": [],
            "required_fixture_case_ids": [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": ["carry_inputs_defined"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_carry_horizon_notional_review",
            "blocked_by": ["position_notional_usd input"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "define position_notional_usd before diagnostic GMX carry bps",
        },
        {
            "input_id": "rate_sign_convention",
            "input_label": "Rate Sign Convention",
            "status": "fixture_required",
            "input_type": "mapping_policy",
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "required_fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": [
                "nonzero_borrowing_relation_reviewed",
                "side_aware_direction_fixtures",
                "carry_inputs_defined",
            ],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_side_aware_sign_review",
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info nonzero borrowing rate mapping review",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "confirm side-aware pay/receive sign convention before diagnostic carry bps",
        },
        {
            "input_id": "source_helper_inputs",
            "input_label": "Source Helper Inputs",
            "status": "source_inputs_missing",
            "input_type": "source_fields",
            "required_source_inputs": source_inputs_required,
            "required_fixture_case_ids": ["source_helper_inputs_presence"],
            "required_expectation_ids": [],
            "required_decision_check_ids": ["source_helper_inputs_available"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_source_helper_input_review",
            "blocked_by": ["live /markets/info source helper inputs unavailable"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "source GMX helper inputs or equivalent fixtures before diagnostic carry bps",
        },
        {
            "input_id": "display_unit_decision",
            "input_label": "Display Unit Decision",
            "status": "policy_input_required",
            "input_type": "display_policy",
            "required_source_inputs": [],
            "required_fixture_case_ids": [],
            "required_expectation_ids": [],
            "required_decision_check_ids": ["display_unit_decision_recorded"],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_hourly_vs_annualized_display_decision",
            "blocked_by": ["production decision on hourly vs annualized display"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record hourly vs annualized display policy before any diagnostic carry bps",
        },
    ]
    carry_required_source_inputs: list[str] = []
    carry_required_fixture_case_ids: list[str] = []
    carry_required_expectation_ids: list[str] = []
    carry_required_decision_check_ids: list[str] = []
    for carry_input in carry_input_checklist:
        for source_input in carry_input["required_source_inputs"]:
            append_unique(carry_required_source_inputs, source_input)
        for fixture_case_id in carry_input["required_fixture_case_ids"]:
            append_unique(carry_required_fixture_case_ids, fixture_case_id)
        for expectation_id in carry_input["required_expectation_ids"]:
            append_unique(carry_required_expectation_ids, expectation_id)
        for decision_check_id in carry_input["required_decision_check_ids"]:
            append_unique(carry_required_decision_check_ids, decision_check_id)
    carry_readiness_summary = {
        "status": "blocked_for_diagnostic_carry_bps",
        "input_count": len(carry_input_checklist),
        "blocked_input_count": len(carry_input_checklist),
        "manual_approval_count": len(mapping_decision_manual_approval_ids),
        "required_source_inputs": carry_required_source_inputs,
        "required_fixture_case_ids": carry_required_fixture_case_ids,
        "required_expectation_ids": carry_required_expectation_ids,
        "required_decision_check_ids": carry_required_decision_check_ids,
        "required_manual_approval_ids": mapping_decision_manual_approval_ids,
        "blocked_outputs": blocked_outputs,
        "may_emit_carry_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "safe_use": safe_use,
        "next_action": "clear carry inputs, fixtures, source helper fields and manual approvals before diagnostic GMX carry bps",
    }
    carry_source_evidence_checklist = [
        {
            "evidence_id": "holding_period_runtime_input",
            "evidence_label": "Holding Period Runtime Input",
            "evidence_type": "runtime_input",
            "status": "input_required",
            "related_input_ids": ["holding_period_hours"],
            "required_source_inputs": [],
            "required_fixture_case_ids": [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": ["carry_inputs_defined"],
            "required_manual_approval_ids": ["gmx_carry_horizon_notional_review"],
            "blocked_by": ["holding_period_hours input"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record holding_period_hours as an explicit runtime input before diagnostic GMX carry bps",
        },
        {
            "evidence_id": "position_notional_runtime_input",
            "evidence_label": "Position Notional Runtime Input",
            "evidence_type": "runtime_input",
            "status": "input_required",
            "related_input_ids": ["position_notional_usd"],
            "required_source_inputs": [],
            "required_fixture_case_ids": [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": ["carry_inputs_defined"],
            "required_manual_approval_ids": ["gmx_carry_horizon_notional_review"],
            "blocked_by": ["position_notional_usd input"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record position_notional_usd as an explicit runtime input before diagnostic GMX carry bps",
        },
        {
            "evidence_id": "side_aware_sign_fixture_evidence",
            "evidence_label": "Side-aware Sign Fixture Evidence",
            "evidence_type": "fixture_case",
            "status": "fixture_required",
            "related_input_ids": ["rate_sign_convention"],
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "required_fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": [
                "nonzero_borrowing_relation_reviewed",
                "side_aware_direction_fixtures",
            ],
            "required_manual_approval_ids": ["gmx_side_aware_sign_review"],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info nonzero borrowing rate mapping review",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "attach side-aware longsPayShorts fixture evidence before diagnostic carry bps",
        },
        {
            "evidence_id": "source_helper_field_evidence",
            "evidence_label": "Source Helper Field Evidence",
            "evidence_type": "source_field",
            "status": "source_inputs_missing",
            "related_input_ids": ["source_helper_inputs", "rate_sign_convention"],
            "required_source_inputs": source_inputs_required,
            "required_fixture_case_ids": ["source_helper_inputs_presence"],
            "required_expectation_ids": [],
            "required_decision_check_ids": [
                "source_helper_inputs_available",
                "nonzero_borrowing_relation_reviewed",
            ],
            "required_manual_approval_ids": [
                "gmx_source_helper_input_review",
                "gmx_live_nonzero_borrowing_mapping_review",
            ],
            "blocked_by": [
                "live /markets/info source helper inputs unavailable",
                "live /markets/info nonzero borrowing rate mapping review",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "collect source helper fields or equivalent fixtures before diagnostic carry bps",
        },
        {
            "evidence_id": "display_unit_policy_evidence",
            "evidence_label": "Display Unit Policy Evidence",
            "evidence_type": "policy_decision",
            "status": "policy_input_required",
            "related_input_ids": ["display_unit_decision"],
            "required_source_inputs": [],
            "required_fixture_case_ids": [],
            "required_expectation_ids": [],
            "required_decision_check_ids": ["display_unit_decision_recorded"],
            "required_manual_approval_ids": ["gmx_hourly_vs_annualized_display_decision"],
            "blocked_by": ["production decision on hourly vs annualized display"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record hourly vs annualized display policy before any diagnostic carry bps",
        },
        {
            "evidence_id": "carry_manual_approval_evidence",
            "evidence_label": "Carry Manual Approval Evidence",
            "evidence_type": "manual_approval",
            "status": "manual_approval_required",
            "related_input_ids": [
                "holding_period_hours",
                "position_notional_usd",
                "rate_sign_convention",
                "source_helper_inputs",
                "display_unit_decision",
            ],
            "required_source_inputs": source_inputs_required,
            "required_fixture_case_ids": carry_required_fixture_case_ids,
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": carry_required_decision_check_ids,
            "required_manual_approval_ids": mapping_decision_manual_approval_ids,
            "blocked_by": ["manual GMX carry approval gate"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "complete manual carry approvals after source and fixture evidence is attached",
        },
    ]
    carry_source_evidence_ids: list[str] = []
    carry_source_evidence_type_ids: list[str] = []
    carry_source_evidence_input_ids: list[str] = []
    carry_source_evidence_source_inputs: list[str] = []
    carry_source_evidence_fixture_case_ids: list[str] = []
    carry_source_evidence_expectation_ids: list[str] = []
    carry_source_evidence_decision_check_ids: list[str] = []
    carry_source_evidence_manual_approval_ids: list[str] = []
    for evidence in carry_source_evidence_checklist:
        append_unique(carry_source_evidence_ids, evidence["evidence_id"])
        append_unique(carry_source_evidence_type_ids, evidence["evidence_type"])
        for input_id in evidence["related_input_ids"]:
            append_unique(carry_source_evidence_input_ids, input_id)
        for source_input in evidence["required_source_inputs"]:
            append_unique(carry_source_evidence_source_inputs, source_input)
        for fixture_case_id in evidence["required_fixture_case_ids"]:
            append_unique(carry_source_evidence_fixture_case_ids, fixture_case_id)
        for expectation_id in evidence["required_expectation_ids"]:
            append_unique(carry_source_evidence_expectation_ids, expectation_id)
        for decision_check_id in evidence["required_decision_check_ids"]:
            append_unique(carry_source_evidence_decision_check_ids, decision_check_id)
        for manual_approval_id in evidence["required_manual_approval_ids"]:
            append_unique(carry_source_evidence_manual_approval_ids, manual_approval_id)
    carry_source_evidence_manual_approval_ids = [
        approval_id
        for approval_id in mapping_decision_manual_approval_ids
        if approval_id in carry_source_evidence_manual_approval_ids
    ]
    carry_source_evidence_summary = {
        "status": "evidence_required",
        "evidence_count": len(carry_source_evidence_checklist),
        "blocked_evidence_count": len(carry_source_evidence_checklist),
        "evidence_ids": carry_source_evidence_ids,
        "evidence_type_ids": carry_source_evidence_type_ids,
        "input_ids": carry_source_evidence_input_ids,
        "required_source_inputs": carry_source_evidence_source_inputs,
        "required_fixture_case_ids": carry_source_evidence_fixture_case_ids,
        "required_expectation_ids": carry_source_evidence_expectation_ids,
        "required_decision_check_ids": carry_source_evidence_decision_check_ids,
        "required_manual_approval_ids": carry_source_evidence_manual_approval_ids,
        "blocked_outputs": blocked_outputs,
        "may_emit_carry_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "safe_use": safe_use,
        "next_action": "attach source, fixture, runtime and manual approval evidence before diagnostic GMX carry bps",
    }
    live_rate_output_fields = [
        "fundingRateLong",
        "fundingRateShort",
        "borrowingRateLong",
        "borrowingRateShort",
        "netRateLong",
        "netRateShort",
    ]
    live_helper_source_checklist = [
        {
            "review_id": "live_rate_output_fields_available",
            "review_label": "Live Rate Output Fields Available",
            "status": "raw_outputs_available",
            "source_scope": "live_markets_info_rate_outputs",
            "evidence_count": len(live_observed),
            "observed_source_fields": live_rate_output_fields,
            "required_source_inputs": [],
            "present_source_inputs": [],
            "missing_source_inputs": source_inputs_required,
            "diagnostic_field_ids": ["rate_relation_summary", "rate_relation_diagnostics"],
            "fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
            ],
            "expectation_ids": [],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_live_nonzero_borrowing_mapping_review",
            "blocked_by": [
                "live /markets/info helper source fields unavailable",
                "live /markets/info nonzero borrowing rate mapping review",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "keep raw ticker rate outputs as evidence only until helper inputs are sourced",
        },
        {
            "review_id": "nonzero_borrowing_relation_evidence",
            "review_label": "Nonzero Borrowing Relation Evidence",
            "status": "mapping_review_required",
            "source_scope": "live_markets_info_relation_evidence",
            "evidence_count": fixture_evidence_count(
                [
                    "live_nonzero_borrowing_raw_sum_relation_observed",
                    "live_shape_offline_fixture",
                ]
            ),
            "observed_source_fields": live_rate_output_fields,
            "required_source_inputs": source_inputs_required,
            "present_source_inputs": [],
            "missing_source_inputs": source_inputs_required,
            "diagnostic_field_ids": ["rate_relation_summary", "rate_relation_diagnostics"],
            "fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
            ],
            "expectation_ids": [],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_live_nonzero_borrowing_mapping_review",
            "blocked_by": [
                "live /markets/info nonzero borrowing rate mapping review",
                "broader live fixture coverage across market states",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "reconcile observed funding+borrowing relation against source helper semantics",
        },
        {
            "review_id": "helper_source_fields_presence",
            "review_label": "Helper Source Fields Presence",
            "status": "source_inputs_missing",
            "source_scope": "live_markets_info_helper_inputs",
            "evidence_count": 0,
            "observed_source_fields": [],
            "required_source_inputs": source_inputs_required,
            "present_source_inputs": [],
            "missing_source_inputs": source_inputs_required,
            "diagnostic_field_ids": ["rate_source_fields_status", "rate_source_fields_summary"],
            "fixture_case_ids": ["source_helper_inputs_presence"],
            "expectation_ids": [],
            "manual_approval_required": True,
            "manual_approval_id": "gmx_source_helper_input_review",
            "blocked_by": ["live /markets/info source helper inputs unavailable"],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "source helper inputs or equivalent fixture artifacts before carry conversion",
        },
        {
            "review_id": "side_direction_helper_fields",
            "review_label": "Side Direction Helper Fields",
            "status": "fixture_required",
            "source_scope": "longs_pay_shorts_direction",
            "evidence_count": 0,
            "observed_source_fields": [],
            "required_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "present_source_inputs": [],
            "missing_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "diagnostic_field_ids": ["rate_source_fields_status", "rate_source_fields_summary"],
            "fixture_case_ids": ["longs_pay_shorts_direction"],
            "expectation_ids": side_aware_expectation_ids,
            "manual_approval_required": True,
            "manual_approval_id": "gmx_side_aware_sign_review",
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "cover long/short paying and receiving direction before carry bps",
        },
        {
            "review_id": "manual_live_helper_mapping_review",
            "review_label": "Manual Live Helper Mapping Review",
            "status": "manual_approval_required",
            "source_scope": "manual_review_gate",
            "evidence_count": 0,
            "observed_source_fields": live_rate_output_fields,
            "required_source_inputs": source_inputs_required,
            "present_source_inputs": [],
            "missing_source_inputs": source_inputs_required,
            "diagnostic_field_ids": diagnostic_field_ids,
            "fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
                "longs_pay_shorts_direction",
                "source_helper_inputs_presence",
            ],
            "expectation_ids": side_aware_expectation_ids,
            "manual_approval_required": True,
            "manual_approval_id": "gmx_live_helper_source_review",
            "blocked_by": [
                "manual GMX live helper source review",
                "live /markets/info source helper inputs unavailable",
                "side-aware funding sign tests",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "approve live helper/source mapping only after source fields, fixtures and side direction evidence are attached",
        },
    ]
    live_helper_review_ids: list[str] = []
    live_helper_review_statuses: list[str] = []
    live_helper_observed_source_fields: list[str] = []
    live_helper_required_source_inputs: list[str] = []
    live_helper_present_source_inputs: list[str] = []
    live_helper_missing_source_inputs: list[str] = []
    live_helper_diagnostic_field_ids: list[str] = []
    live_helper_fixture_case_ids: list[str] = []
    live_helper_expectation_ids: list[str] = []
    live_helper_manual_approval_ids: list[str] = []
    for review in live_helper_source_checklist:
        append_unique(live_helper_review_ids, review["review_id"])
        append_unique(live_helper_review_statuses, review["status"])
        for field_id in review["observed_source_fields"]:
            append_unique(live_helper_observed_source_fields, field_id)
        for source_input in review["required_source_inputs"]:
            append_unique(live_helper_required_source_inputs, source_input)
        for source_input in review["present_source_inputs"]:
            append_unique(live_helper_present_source_inputs, source_input)
        for source_input in review["missing_source_inputs"]:
            append_unique(live_helper_missing_source_inputs, source_input)
        for field_id in review["diagnostic_field_ids"]:
            append_unique(live_helper_diagnostic_field_ids, field_id)
        for fixture_case_id in review["fixture_case_ids"]:
            append_unique(live_helper_fixture_case_ids, fixture_case_id)
        for expectation_id in review["expectation_ids"]:
            append_unique(live_helper_expectation_ids, expectation_id)
        if review["manual_approval_required"]:
            append_unique(live_helper_manual_approval_ids, review["manual_approval_id"])
    live_helper_source_summary = {
        "status": "helper_source_review_required",
        "review_count": len(live_helper_source_checklist),
        "blocked_review_count": len(live_helper_source_checklist),
        "review_ids": live_helper_review_ids,
        "review_statuses": live_helper_review_statuses,
        "observed_source_fields": live_helper_observed_source_fields,
        "required_source_inputs": live_helper_required_source_inputs,
        "present_source_inputs": live_helper_present_source_inputs,
        "missing_source_inputs": live_helper_missing_source_inputs,
        "diagnostic_field_ids": live_helper_diagnostic_field_ids,
        "fixture_case_ids": live_helper_fixture_case_ids,
        "expectation_ids": live_helper_expectation_ids,
        "manual_approval_ids": live_helper_manual_approval_ids,
        "blocked_outputs": blocked_outputs,
        "may_emit_carry_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "safe_use": safe_use,
        "next_action": "complete live helper/source review before diagnostic GMX carry bps",
    }
    helper_source_follow_up_checklist = [
        {
            "follow_up_id": "source_helper_inputs_missing",
            "follow_up_label": "Source Helper Inputs Missing",
            "follow_up_type": "missing_source_input",
            "status": "source_inputs_missing",
            "related_input_ids": ["source_helper_inputs", "rate_sign_convention"],
            "related_review_ids": ["helper_source_fields_presence", "manual_live_helper_mapping_review"],
            "missing_source_inputs": source_inputs_required,
            "required_fixture_case_ids": ["source_helper_inputs_presence"],
            "required_expectation_ids": [],
            "required_decision_check_ids": ["source_helper_inputs_available"],
            "blocking_manual_approval_ids": [
                "gmx_source_helper_input_review",
                "gmx_live_helper_source_review",
            ],
            "blocked_by": [
                "live /markets/info source helper inputs unavailable",
                "manual GMX live helper source review",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "source missing helper inputs or equivalent fixtures before GMX carry conversion",
        },
        {
            "follow_up_id": "live_nonzero_mapping_approval",
            "follow_up_label": "Live Nonzero Mapping Approval",
            "follow_up_type": "manual_approval",
            "status": "mapping_review_required",
            "related_input_ids": ["source_helper_inputs", "rate_sign_convention"],
            "related_review_ids": [
                "live_rate_output_fields_available",
                "nonzero_borrowing_relation_evidence",
            ],
            "missing_source_inputs": source_inputs_required,
            "required_fixture_case_ids": [
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
            ],
            "required_expectation_ids": [],
            "required_decision_check_ids": [
                "nonzero_borrowing_relation_reviewed",
                "source_helper_inputs_available",
            ],
            "blocking_manual_approval_ids": ["gmx_live_nonzero_borrowing_mapping_review"],
            "blocked_by": [
                "live /markets/info nonzero borrowing rate mapping review",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "resolve live funding+borrowing mapping before any carry conversion",
        },
        {
            "follow_up_id": "side_direction_approval",
            "follow_up_label": "Side Direction Approval",
            "follow_up_type": "fixture_manual_approval",
            "status": "fixture_required",
            "related_input_ids": ["rate_sign_convention"],
            "related_review_ids": ["side_direction_helper_fields"],
            "missing_source_inputs": ["fundingFactorPerSecond", "longsPayShorts"],
            "required_fixture_case_ids": ["longs_pay_shorts_direction"],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": ["side_aware_direction_fixtures"],
            "blocking_manual_approval_ids": ["gmx_side_aware_sign_review"],
            "blocked_by": [
                "side-aware funding sign tests",
                "live /markets/info source helper inputs unavailable",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "approve side-aware long/short funding direction only after fixtures exist",
        },
        {
            "follow_up_id": "carry_runtime_policy_approvals",
            "follow_up_label": "Carry Runtime And Policy Approvals",
            "follow_up_type": "carry_boundary_approval",
            "status": "manual_approval_required",
            "related_input_ids": [
                "holding_period_hours",
                "position_notional_usd",
                "display_unit_decision",
            ],
            "related_review_ids": ["carry_conversion_boundary"],
            "missing_source_inputs": [],
            "required_fixture_case_ids": [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
            ],
            "required_expectation_ids": side_aware_expectation_ids,
            "required_decision_check_ids": [
                "carry_inputs_defined",
                "display_unit_decision_recorded",
            ],
            "blocking_manual_approval_ids": [
                "gmx_carry_horizon_notional_review",
                "gmx_hourly_vs_annualized_display_decision",
            ],
            "blocked_by": [
                "holding_period_hours input",
                "position_notional_usd input",
                "production decision on hourly vs annualized display",
            ],
            "blocked_outputs": blocked_outputs,
            "may_emit_carry_bps": False,
            "may_estimate_cost_bps": False,
            "may_rank_routes": False,
            "may_submit_orders": False,
            "safe_use": safe_use,
            "next_action": "record runtime carry inputs and display policy before carry conversion",
        },
    ]
    helper_source_follow_up_ids: list[str] = []
    helper_source_follow_up_statuses: list[str] = []
    helper_source_follow_up_input_ids: list[str] = []
    helper_source_follow_up_review_ids: list[str] = []
    helper_source_follow_up_missing_inputs: list[str] = []
    helper_source_follow_up_fixture_case_ids: list[str] = []
    helper_source_follow_up_expectation_ids: list[str] = []
    helper_source_follow_up_decision_check_ids: list[str] = []
    helper_source_follow_up_manual_approval_ids: list[str] = []
    for follow_up in helper_source_follow_up_checklist:
        append_unique(helper_source_follow_up_ids, follow_up["follow_up_id"])
        append_unique(helper_source_follow_up_statuses, follow_up["status"])
        for input_id in follow_up["related_input_ids"]:
            append_unique(helper_source_follow_up_input_ids, input_id)
        for review_id in follow_up["related_review_ids"]:
            append_unique(helper_source_follow_up_review_ids, review_id)
        for source_input in follow_up["missing_source_inputs"]:
            append_unique(helper_source_follow_up_missing_inputs, source_input)
        for fixture_case_id in follow_up["required_fixture_case_ids"]:
            append_unique(helper_source_follow_up_fixture_case_ids, fixture_case_id)
        for expectation_id in follow_up["required_expectation_ids"]:
            append_unique(helper_source_follow_up_expectation_ids, expectation_id)
        for decision_check_id in follow_up["required_decision_check_ids"]:
            append_unique(helper_source_follow_up_decision_check_ids, decision_check_id)
        for manual_approval_id in follow_up["blocking_manual_approval_ids"]:
            append_unique(helper_source_follow_up_manual_approval_ids, manual_approval_id)
    helper_source_follow_up_summary = {
        "status": "follow_up_required",
        "follow_up_count": len(helper_source_follow_up_checklist),
        "blocked_follow_up_count": len(helper_source_follow_up_checklist),
        "follow_up_ids": helper_source_follow_up_ids,
        "follow_up_statuses": helper_source_follow_up_statuses,
        "related_input_ids": helper_source_follow_up_input_ids,
        "related_review_ids": helper_source_follow_up_review_ids,
        "missing_source_inputs": helper_source_follow_up_missing_inputs,
        "required_fixture_case_ids": helper_source_follow_up_fixture_case_ids,
        "required_expectation_ids": helper_source_follow_up_expectation_ids,
        "required_decision_check_ids": helper_source_follow_up_decision_check_ids,
        "blocking_manual_approval_ids": helper_source_follow_up_manual_approval_ids,
        "blocked_outputs": blocked_outputs,
        "may_emit_carry_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "safe_use": safe_use,
        "next_action": "close helper/source follow-up rows before any GMX carry conversion",
    }

    return {
        "status": "mapping_review_required",
        "read_only": True,
        "source_relation_status": source_relation_status,
        "live_mapping_status": mapping_review.get("status", "source_vs_live_mapping_unresolved"),
        "source_confirmed_count": len(source_confirmed),
        "live_observed_count": len(live_observed),
        "fixture_coverage_count": len(fixture_coverage_ids),
        "diagnostic_field_ids": diagnostic_field_ids,
        "source_inputs_required": source_inputs_required,
        "fixture_coverage_ids": fixture_coverage_ids,
        "blocked_outputs": blocked_outputs,
        "may_emit_carry_bps": False,
        "may_estimate_cost_bps": False,
        "may_rank_routes": False,
        "may_submit_orders": False,
        "safe_use": safe_use,
        "next_action": gmx_rate_semantics.get("next_action") or "map live GMX rate semantics before carry bps",
        "review_items": review_items,
        "blocker_breakdown": list(blocker_groups.values()),
        "fixture_readiness_matrix": fixture_readiness_matrix,
        "side_aware_fixture_expectations": side_aware_fixture_expectations,
        "mapping_decision_checklist": mapping_decision_checklist,
        "carry_readiness_summary": carry_readiness_summary,
        "carry_input_checklist": carry_input_checklist,
        "carry_source_evidence_summary": carry_source_evidence_summary,
        "carry_source_evidence_checklist": carry_source_evidence_checklist,
        "live_helper_source_summary": live_helper_source_summary,
        "live_helper_source_checklist": live_helper_source_checklist,
        "helper_source_follow_up_summary": helper_source_follow_up_summary,
        "helper_source_follow_up_checklist": helper_source_follow_up_checklist,
    }


PERP_DEX_ROUTE_MODEL["diagnostic_cost_estimate_v0"]["summary"] = _build_diagnostic_cost_summary(
    PERP_DEX_ROUTE_MODEL["diagnostic_cost_estimate_v0"],
    PERP_DEX_ROUTE_MODEL["required_inputs"],
    PERP_DEX_ROUTE_MODEL["gmx_rate_semantics"],
)
PERP_DEX_ROUTE_MODEL["gmx_rate_mapping_review_v0"] = _build_gmx_rate_mapping_review(
    PERP_DEX_ROUTE_MODEL["gmx_rate_semantics"]
)


async def get_hyperliquid_client() -> AsyncGenerator[HyperliquidClient, None]:
    client = HyperliquidClient()
    try:
        yield client
    finally:
        await client.close()


async def get_dydx_client() -> AsyncGenerator[DydxClient, None]:
    client = DydxClient()
    try:
        yield client
    finally:
        await client.close()


async def get_gmx_client() -> AsyncGenerator[GmxClient, None]:
    client = GmxClient()
    try:
        yield client
    finally:
        await client.close()


async def get_lighter_client() -> AsyncGenerator[LighterClient, None]:
    client = LighterClient()
    try:
        yield client
    finally:
        await client.close()


async def get_aster_client() -> AsyncGenerator[AsterClient, None]:
    client = AsterClient()
    try:
        yield client
    finally:
        await client.close()


async def get_coinglass_client() -> AsyncGenerator[CoinGlassClient, None]:
    client = CoinGlassClient()
    try:
        yield client
    finally:
        await client.close()


def _parse_symbols(symbols: Optional[str]) -> tuple[str, ...]:
    raw = symbols or ",".join(DEFAULT_HYPERLIQUID_SYMBOLS)
    parsed = tuple(dict.fromkeys(item.strip().upper() for item in raw.split(",") if item.strip()))
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="symbols must contain at least one symbol",
        )
    if len(parsed) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="symbols must contain 20 or fewer symbols",
        )
    return parsed


def _parse_coinglass_exchanges(exchanges: Optional[str]) -> tuple[str, ...]:
    raw = exchanges or ",".join(DEFAULT_COINGLASS_PERP_DEX_EXCHANGES)
    allowed = {
        exchange.casefold(): exchange
        for exchange in COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES
    }
    parsed: list[str] = []
    invalid: list[str] = []
    for item in (value.strip() for value in raw.split(",")):
        if not item:
            continue
        canonical = allowed.get(item.casefold())
        if canonical is None:
            invalid.append(item)
            continue
        if canonical not in parsed:
            parsed.append(canonical)

    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "unsupported CoinGlass Perp DEX exchange(s): "
                f"{', '.join(invalid)}; supported candidates: {', '.join(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES)}"
            ),
        )
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="exchanges must contain at least one CoinGlass Perp DEX candidate",
        )
    if len(parsed) > len(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"exchanges must contain {len(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES)} or fewer values",
        )
    return tuple(parsed)


def _dedupe_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _provider_error_class_from_exception(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code if exc.response is not None else None
        if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            return "rate_limit"
        if status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_410_GONE):
            return "unavailable_endpoint"
        if status_code == status.HTTP_408_REQUEST_TIMEOUT:
            return "timeout"
        if status_code is not None and status_code >= 500:
            return "provider_unavailable"
        return "provider_http_error"
    if isinstance(exc, (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError)):
        return "provider_unavailable"
    if isinstance(exc, ValueError):
        return "schema_drift"
    return "provider_unavailable"


def _provider_error_class_from_snapshot(snapshot: dict[str, Any]) -> str | None:
    markets = snapshot.get("markets") if isinstance(snapshot.get("markets"), list) else []
    reason = str(snapshot.get("reason") or "")
    if reason in DIRECT_VENUE_SCHEMA_DRIFT_REASONS:
        return "schema_drift"
    if snapshot.get("status") == "empty" or not markets:
        return "empty_response"
    return None


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _build_depth_freshness_evidence(
    snapshot: dict[str, Any],
    *,
    depth_market_count: int,
    observed_at: datetime | None = None,
) -> dict[str, Any]:
    observed = observed_at or datetime.now(timezone.utc)
    fetched_at = snapshot.get("fetched_at")
    parsed_fetched_at = _parse_iso_datetime(fetched_at)
    age_ms = None
    if parsed_fetched_at is not None:
        age_ms = max(0, int((observed - parsed_fetched_at).total_seconds() * 1000))

    if depth_market_count <= 0:
        freshness_status = "not_applicable"
        evidence_status = "no_depth_diagnostics"
    elif parsed_fetched_at is None:
        freshness_status = "timestamp_missing"
        evidence_status = "timestamp_required"
    elif age_ms is not None and age_ms <= DIRECT_VENUE_DEPTH_FRESHNESS_MAX_AGE_MS:
        freshness_status = "fresh_for_display"
        evidence_status = "timestamp_available"
    else:
        freshness_status = "stale_for_display"
        evidence_status = "stale_timestamp"

    return {
        "status": freshness_status,
        "evidence_status": evidence_status,
        "snapshot_timestamp": fetched_at,
        "observed_at": observed.isoformat(),
        "age_ms": age_ms,
        "max_age_ms": DIRECT_VENUE_DEPTH_FRESHNESS_MAX_AGE_MS,
        "depth_market_count": depth_market_count,
        "required_policy_inputs": [
            "depth_snapshot_timestamp",
            "max_depth_age_ms",
            "stale_depth_action",
        ],
        "stale_depth_action": "display_warning_only_until_route_policy_decision",
        "may_emit_slippage_bps": False,
        "numeric_total_status": "blocked",
        "safe_use": "depth freshness evidence only; do not estimate slippage, route cost or ranking",
    }


def _build_direct_venue_availability_summary(
    snapshot: dict[str, Any],
    *,
    source: str,
    requested_symbols: tuple[str, ...],
    provider_error_class: str | None = None,
) -> dict[str, Any]:
    markets = snapshot.get("markets") if isinstance(snapshot.get("markets"), list) else []
    matched_symbols = _dedupe_strings(
        [
            str(market.get("symbol") or "").upper()
            for market in markets
            if isinstance(market, dict)
        ]
    )
    requested = list(requested_symbols)
    missing_symbols = [symbol for symbol in requested if symbol not in matched_symbols]
    market_status_counts: dict[str, int] = {}
    provider_status_counts: dict[str, int] = {}
    depth_statuses: list[str] = []
    for market in markets:
        if not isinstance(market, dict):
            continue
        market_status = str(market.get("status") or "unknown")
        provider_status = str(market.get("provider_status") or "unknown")
        market_status_counts[market_status] = market_status_counts.get(market_status, 0) + 1
        provider_status_counts[provider_status] = provider_status_counts.get(provider_status, 0) + 1
        depth_status = market.get("orderbook_depth_status")
        if depth_status:
            depth_statuses.append(str(depth_status))

    error_class = provider_error_class or _provider_error_class_from_snapshot(snapshot)
    if error_class is not None and error_class not in DIRECT_VENUE_PROVIDER_ERROR_CLASSES:
        error_class = "provider_unavailable"

    return {
        "venue_id": snapshot.get("venue_id") or source,
        "venue_name": snapshot.get("venue_name") or source,
        "source": snapshot.get("source"),
        "status": snapshot.get("status") or "unavailable",
        "provider_error_class": error_class,
        "rows": len(markets),
        "requested_symbols": requested,
        "matched_symbols": matched_symbols,
        "missing_symbols": missing_symbols,
        "market_status_counts": market_status_counts,
        "provider_status_counts": provider_status_counts,
        "read_only": snapshot.get("read_only") is True,
        "execution_enabled": snapshot.get("execution_enabled") is True,
        "ranking_enabled": snapshot.get("ranking_enabled") is True,
        "production_signal_enabled": snapshot.get("production_signal_enabled") is True,
        "normalization_status": snapshot.get("normalization_status"),
        "depth_diagnostics": {
            "available": bool(depth_statuses),
            "market_count": len(depth_statuses),
            "statuses": sorted(set(depth_statuses)),
            "freshness": _build_depth_freshness_evidence(
                snapshot,
                depth_market_count=len(depth_statuses),
            ),
        },
        "fetched_at": snapshot.get("fetched_at"),
        "reason": snapshot.get("reason"),
        "safe_use": "direct public market context only; do not route, rank liquidity or submit orders",
    }


def _with_direct_venue_availability_summary(
    snapshot: dict[str, Any],
    *,
    source: str,
    requested_symbols: tuple[str, ...],
) -> dict[str, Any]:
    result = dict(snapshot)
    result["availability_summary"] = _build_direct_venue_availability_summary(
        result,
        source=source,
        requested_symbols=requested_symbols,
    )
    return result


def _direct_venue_provider_error_detail(
    *,
    source: str,
    requested_symbols: tuple[str, ...],
    exc: Exception,
) -> dict[str, Any]:
    provider_error_class = _provider_error_class_from_exception(exc)
    http_status = (
        exc.response.status_code
        if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None
        else None
    )
    snapshot = {
        "venue_id": source,
        "venue_name": source,
        "source": source,
        "status": "unavailable",
        "requested_symbols": list(requested_symbols),
        "markets": [],
        "read_only": True,
        "execution_enabled": False,
        "reason": provider_error_class,
    }
    return {
        "message": f"{source} market snapshot request failed",
        "source": source,
        "provider_error_class": provider_error_class,
        "provider_http_status": http_status,
        "read_only": True,
        "execution_enabled": False,
        "ranking_enabled": False,
        "production_signal_enabled": False,
        "availability_summary": _build_direct_venue_availability_summary(
            snapshot,
            source=source,
            requested_symbols=requested_symbols,
            provider_error_class=provider_error_class,
        ),
    }


@router.get("/route-constraints", response_model=ApiResponse)
async def get_route_constraints():
    """Read-only Perp DEX route and execution constraints policy."""
    return ApiResponse(
        data=PERP_DEX_ROUTE_CONSTRAINTS,
        meta={
            "read_only": True,
            "external_provider_calls": False,
            "source": "deltagrid_perp_dex_policy",
        },
    )


@router.get("/route-model", response_model=ApiResponse)
async def get_route_model():
    """Read-only Perp DEX route-level cost model contract."""
    return ApiResponse(
        data=PERP_DEX_ROUTE_MODEL,
        meta={
            "read_only": True,
            "external_provider_calls": False,
            "source": "deltagrid_perp_dex_route_model",
        },
    )


@router.get("/venues/coinglass/markets", response_model=ApiResponse)
async def get_coinglass_perp_dex_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    exchanges: Optional[str] = Query(
        None,
        description="Comma-separated CoinGlass futures exchanges for Perp DEX research enrichment.",
    ),
    client: CoinGlassClient = Depends(get_coinglass_client),
):
    """Read-only CoinGlass Perp DEX third-party enrichment snapshot."""
    parsed_symbols = _parse_symbols(symbols or ",".join(DEFAULT_COINGLASS_SYMBOLS))
    parsed_exchanges = _parse_coinglass_exchanges(exchanges)

    try:
        snapshot = await client.fetch_perp_dex_market_snapshot(parsed_symbols, parsed_exchanges)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CoinGlass Perp DEX enrichment request failed: {exc}",
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "coinglass",
            "requested_symbols": list(parsed_symbols),
            "requested_exchanges": list(parsed_exchanges),
            "candidate_exchanges": list(COINGLASS_PERP_DEX_CANDIDATE_EXCHANGES),
            "normalization_status": snapshot.get("normalization_status"),
            "coverage_summary": snapshot.get("coverage_summary"),
            "ranking_enabled": False,
            "production_signal_enabled": False,
        },
    )


@router.get("/venues/aster/markets", response_model=ApiResponse)
async def get_aster_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    client: AsterClient = Depends(get_aster_client),
):
    """Read-only live Aster market snapshot."""
    parsed_symbols = _parse_symbols(symbols or ",".join(DEFAULT_ASTER_SYMBOLS))

    try:
        snapshot = await client.fetch_market_snapshot(parsed_symbols)
        snapshot = _with_direct_venue_availability_summary(
            snapshot,
            source="aster",
            requested_symbols=parsed_symbols,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_direct_venue_provider_error_detail(
                source="aster",
                requested_symbols=parsed_symbols,
                exc=exc,
            ),
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "aster",
            "requested_symbols": list(parsed_symbols),
            "normalization_status": "aster_public_futures_market_data",
            "availability_summary": snapshot.get("availability_summary"),
        },
    )


@router.get("/venues/lighter/markets", response_model=ApiResponse)
async def get_lighter_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    client: LighterClient = Depends(get_lighter_client),
):
    """Read-only live Lighter market snapshot."""
    parsed_symbols = _parse_symbols(symbols or ",".join(DEFAULT_LIGHTER_SYMBOLS))

    try:
        snapshot = await client.fetch_market_snapshot(parsed_symbols)
        snapshot = _with_direct_venue_availability_summary(
            snapshot,
            source="lighter",
            requested_symbols=parsed_symbols,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_direct_venue_provider_error_detail(
                source="lighter",
                requested_symbols=parsed_symbols,
                exc=exc,
            ),
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "lighter",
            "requested_symbols": list(parsed_symbols),
            "normalization_status": "lighter_public_market_details",
            "availability_summary": snapshot.get("availability_summary"),
        },
    )


@router.get("/venues/hyperliquid/markets", response_model=ApiResponse)
async def get_hyperliquid_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    dex: str = Query("", description="Optional Hyperliquid dex selector for HIP-3 deployments."),
    client: HyperliquidClient = Depends(get_hyperliquid_client),
):
    """Read-only live Hyperliquid market snapshot."""
    parsed_symbols = _parse_symbols(symbols)
    normalized_dex = dex.strip()

    try:
        snapshot = await client.fetch_market_snapshot(parsed_symbols, dex=normalized_dex)
        snapshot = _with_direct_venue_availability_summary(
            snapshot,
            source="hyperliquid",
            requested_symbols=parsed_symbols,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_direct_venue_provider_error_detail(
                source="hyperliquid",
                requested_symbols=parsed_symbols,
                exc=exc,
            ),
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "hyperliquid",
            "requested_symbols": list(parsed_symbols),
            "availability_summary": snapshot.get("availability_summary"),
        },
    )


@router.get("/venues/gmx/markets", response_model=ApiResponse)
async def get_gmx_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    client: GmxClient = Depends(get_gmx_client),
):
    """Read-only raw GMX market snapshot."""
    parsed_symbols = _parse_symbols(symbols or ",".join(DEFAULT_GMX_SYMBOLS))

    try:
        snapshot = await client.fetch_market_snapshot(parsed_symbols)
        snapshot = _with_direct_venue_availability_summary(
            snapshot,
            source="gmx",
            requested_symbols=parsed_symbols,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_direct_venue_provider_error_detail(
                source="gmx",
                requested_symbols=parsed_symbols,
                exc=exc,
            ),
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "gmx",
            "requested_symbols": list(parsed_symbols),
            "normalization_status": snapshot.get("normalization_status"),
            "scale_validation_status": snapshot.get("scale_validation_status"),
            "token_amount_scale_status": snapshot.get("token_amount_scale_status"),
            "diagnostic_usd_scale_status": snapshot.get("diagnostic_usd_scale_status"),
            "rate_semantics_status": snapshot.get("rate_semantics_status"),
            "rate_relation_summary": snapshot.get("rate_relation_summary"),
            "rate_source_fields_status": snapshot.get("rate_source_fields_status"),
            "rate_source_fields_summary": snapshot.get("rate_source_fields_summary"),
            "availability_summary": snapshot.get("availability_summary"),
        },
    )


@router.get("/venues/dydx/markets", response_model=ApiResponse)
async def get_dydx_markets(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols."),
    client: DydxClient = Depends(get_dydx_client),
):
    """Read-only live dYdX market snapshot."""
    parsed_symbols = _parse_symbols(symbols or ",".join(DEFAULT_DYDX_SYMBOLS))

    try:
        snapshot = await client.fetch_market_snapshot(parsed_symbols)
        snapshot = _with_direct_venue_availability_summary(
            snapshot,
            source="dydx",
            requested_symbols=parsed_symbols,
        )
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_direct_venue_provider_error_detail(
                source="dydx",
                requested_symbols=parsed_symbols,
                exc=exc,
            ),
        ) from exc

    return ApiResponse(
        data=snapshot,
        meta={
            "read_only": True,
            "external_provider_calls": True,
            "source": "dydx",
            "requested_symbols": list(parsed_symbols),
            "availability_summary": snapshot.get("availability_summary"),
        },
    )
