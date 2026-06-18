from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import perp_dex


class FakeCoinGlassPerpDexClient:
    async def fetch_perp_dex_market_snapshot(self, symbols: tuple[str, ...], exchanges: tuple[str, ...]) -> dict:
        return {
            "venue_id": "coinglass_perp_dex",
            "venue_name": "CoinGlass Perp DEX",
            "source": "coinglass_futures_coins_markets",
            "status": "live",
            "dex": "coinglass",
            "requested_symbols": list(symbols),
            "requested_exchanges": list(exchanges),
            "candidate_exchanges": ["Hyperliquid", "dYdX", "Aster", "Lighter"],
            "markets": [
                {
                    "symbol": symbols[0],
                    "market": f"{symbols[0]}-PERP aggregate",
                    "venue_id": "coinglass:aster",
                    "venue_name": "Aster",
                    "dex": "Aster",
                    "status": "partial",
                    "provider_status": "third_party_aggregate",
                    "normalization_status": "coinglass_coin_market_enrichment",
                    "mark_price": 100.0,
                    "mid_price": None,
                    "oracle_price": None,
                    "prev_day_price": None,
                    "funding_rate": 0.0001,
                    "funding_pct": 0.01,
                    "open_interest_base": 10.0,
                    "open_interest_usd": 1000.0,
                    "volume_24h_usd": None,
                    "volume_24h_base": None,
                    "premium": None,
                    "premium_pct": None,
                    "impact_bid_price": None,
                    "impact_ask_price": None,
                    "only_isolated": False,
                    "max_leverage": None,
                    "sz_decimals": None,
                    "long_short_ratio_1h": 1.2,
                    "long_short_ratio_24h": None,
                    "long_liquidation_usd_24h": None,
                    "short_liquidation_usd_24h": None,
                    "liquidation_usd_24h": None,
                    "source_endpoint": "/api/futures/coins-markets",
                    "source_exchange": "Aster",
                    "resolution_action": "validate direct venue adapter before route scoring",
                    "resolution_reason": "not execution-grade route input",
                    "fetched_at": "2026-06-17T00:00:00+00:00",
                }
            ],
            "fetched_at": "2026-06-17T00:00:00+00:00",
            "read_only": True,
            "execution_enabled": False,
            "normalization_status": "coinglass_coin_market_enrichment",
            "ranking_enabled": False,
            "production_signal_enabled": False,
            "coverage_summary": {
                "total_rows": 1,
                "exchanges_with_matches": 1,
                "field_groups": ["price", "funding", "open_interest"],
                "field_totals": {"price": 1, "funding": 1, "open_interest": 1},
                "direct_adapter_candidate_hints": ["Aster"],
                "selection_policy": "Coverage hints only",
                "by_exchange": {
                    "Aster": {
                        "status": "partial",
                        "requested_rows": 1,
                        "matched_rows": 1,
                        "matched_symbols": [symbols[0]],
                        "missing_symbols": [],
                        "available_field_groups": ["price", "funding", "open_interest"],
                        "field_coverage": {"price": 1, "funding": 1, "open_interest": 1},
                        "route_input_status": "not_route_input",
                        "next_action": "review official venue API",
                    }
                },
            },
        }


def assert_structured_route_blockers(blockers: list[dict], *, require_scope: bool = False) -> None:
    assert blockers
    for blocker in blockers:
        assert blocker["id"]
        assert blocker["severity"] == "blocker"
        assert blocker["reason"]
        assert blocker["missing_inputs"]
        assert isinstance(blocker["missing_inputs"], list)
        assert blocker["blocked_by"]
        assert isinstance(blocker["blocked_by"], list)
        assert blocker["safe_use"]
        if require_scope:
            assert blocker["scope"]


def assert_structured_route_required_inputs(required_inputs: list[dict]) -> None:
    assert required_inputs
    for item in required_inputs:
        assert item["id"]
        assert item["label"]
        assert item["reason"]


def assert_route_formula_skeleton(formulas: dict[str, str]) -> None:
    assert formulas
    assert set(formulas) == {"gross_edge_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"}
    for formula in formulas.values():
        assert formula


def assert_structured_route_cost_diagnostics(diagnostics: dict) -> None:
    assert diagnostics["status"] == "blocked_for_numeric_total"
    assert diagnostics["read_only"] is True
    assert diagnostics["may_emit_numeric_total_bps"] is False
    assert diagnostics["safe_use"]
    assert diagnostics["next_action"]

    required_components = {
        "lighter_fee_fields",
        "lighter_top_order_depth",
        "aster_published_fee_schedule",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
        "slippage_price_impact",
        "funding_borrow_carry",
    }
    components = diagnostics["components"]
    component_ids = {component["id"] for component in components}
    assert component_ids == required_components
    summary = diagnostics["summary"]
    assert summary["status"] == diagnostics["status"]
    assert summary["boundary"] == "component_readiness_only"
    assert summary["component_count"] == len(components)
    assert summary["display_only_component_count"] == len(
        [component for component in components if component["may_emit_component_bps"]]
    )
    assert summary["blocked_numeric_component_count"] == len(
        [component for component in components if not component["may_emit_component_bps"]]
    )
    assert summary["sourced_component_count"] == len([component for component in components if component["source_fields"]])
    assert summary["component_ids"] == [component["id"] for component in components]
    assert summary["display_component_ids"] == [
        component["id"] for component in components if component["may_emit_component_bps"]
    ]
    assert summary["blocked_numeric_component_ids"] == [
        component["id"] for component in components if not component["may_emit_component_bps"]
    ]
    assert summary["sourced_component_ids"] == [component["id"] for component in components if component["source_fields"]]
    assert summary["may_emit_numeric_total_bps"] is False
    assert summary["numeric_total_status"] == "blocked"
    assert summary["safe_use"] == diagnostics["safe_use"]
    assert summary["next_action"] == diagnostics["next_action"]

    components_by_venue: dict[str, list[dict]] = {}
    for component in components:
        components_by_venue.setdefault(component["venue_id"], []).append(component)
    venue_breakdown = summary["venue_breakdown"]
    assert [item["venue_id"] for item in venue_breakdown] == list(components_by_venue)
    for venue in venue_breakdown:
        venue_components = components_by_venue[venue["venue_id"]]
        assert venue["venue_label"]
        assert venue["component_count"] == len(venue_components)
        assert venue["display_only_component_count"] == len(
            [component for component in venue_components if component["may_emit_component_bps"]]
        )
        assert venue["blocked_numeric_component_count"] == len(
            [component for component in venue_components if not component["may_emit_component_bps"]]
        )
        assert venue["sourced_component_count"] == len(
            [component for component in venue_components if component["source_fields"]]
        )
        assert venue["component_ids"] == [component["id"] for component in venue_components]
        assert venue["display_component_ids"] == [
            component["id"] for component in venue_components if component["may_emit_component_bps"]
        ]
        assert venue["blocked_numeric_component_ids"] == [
            component["id"] for component in venue_components if not component["may_emit_component_bps"]
        ]
        assert venue["sourced_component_ids"] == [component["id"] for component in venue_components if component["source_fields"]]
        assert venue["numeric_total_status"] == "blocked"
        assert venue["safe_use"]

    components_by_blocker: dict[str, list[dict]] = {}
    for component in components:
        for blocker in component["blocked_by"]:
            components_by_blocker.setdefault(blocker, []).append(component)
    blocker_breakdown = summary["blocker_breakdown"]
    assert [item["blocker"] for item in blocker_breakdown] == list(components_by_blocker)
    for blocker in blocker_breakdown:
        blocker_components = components_by_blocker[blocker["blocker"]]
        venue_ids = []
        for component in blocker_components:
            if component["venue_id"] not in venue_ids:
                venue_ids.append(component["venue_id"])
        assert blocker["component_count"] == len(blocker_components)
        assert blocker["component_ids"] == [component["id"] for component in blocker_components]
        assert blocker["venue_ids"] == venue_ids
        assert blocker["display_component_ids"] == [
            component["id"] for component in blocker_components if component["may_emit_component_bps"]
        ]
        assert blocker["blocked_numeric_component_ids"] == [
            component["id"] for component in blocker_components if not component["may_emit_component_bps"]
        ]
        assert blocker["numeric_total_status"] == "blocked"
        assert blocker["safe_use"]

    for component in components:
        assert component["id"]
        assert component["label"]
        assert component["venue_id"]
        assert component["status"]
        assert isinstance(component["source_fields"], list)
        assert isinstance(component["may_emit_component_bps"], bool)
        assert component["required_input_ids"]
        assert isinstance(component["required_input_ids"], list)
        assert component["blocked_by"]
        assert isinstance(component["blocked_by"], list)
        assert component["safe_use"]
        if component["may_emit_component_bps"]:
            assert component["source_fields"]


def test_perp_dex_route_constraints_policy_is_research_only() -> None:
    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/route-constraints")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is False

    policy = payload["data"]
    assert policy["status"] == "research_only"
    assert policy["read_only"] is True
    assert policy["execution_enabled"] is False
    assert policy["production_liquidity_signal"] is False
    assert policy["normalized_snapshot_venues"] == ["hyperliquid", "dydx", "lighter", "aster"]
    assert policy["raw_snapshot_venues"] == ["gmx"]
    assert policy["coinglass_enrichment_venues"] == ["Aster", "Lighter", "EdgeX", "Drift"]
    assert policy["lighter_direct_snapshot"]["status"] == "direct_read_only"
    assert policy["lighter_direct_snapshot"]["read_only"] is True
    assert "https://apidocs.lighter.xyz/reference/orderbookdetails" in policy["lighter_direct_snapshot"]["source_urls"]
    assert "https://apidocs.lighter.xyz/reference/orderbookorders" in policy["lighter_direct_snapshot"]["source_urls"]
    assert "route-level liquidity ranking" in policy["lighter_direct_snapshot"]["blocked_for_production_signal"]
    lighter_semantics = policy["lighter_direct_snapshot"]["cost_input_semantics"]
    assert lighter_semantics["status"] == "diagnostic_metadata_only"
    assert lighter_semantics["fee_inputs"]["status"] == "partial_ready"
    assert "maker_fee" in lighter_semantics["fee_inputs"]["source_fields"]
    assert lighter_semantics["depth_inputs"]["status"] == "partial_ready_top_orders_only"
    assert "orderBookOrders.bids" in lighter_semantics["depth_inputs"]["source_fields"]
    assert "do not estimate slippage" in lighter_semantics["depth_inputs"]["safe_use"]
    assert lighter_semantics["slippage_inputs"]["status"] == "not_modeled"
    assert policy["aster_direct_snapshot"]["status"] == "direct_read_only"
    assert policy["aster_direct_snapshot"]["read_only"] is True
    assert "https://asterdex.github.io/aster-api-website/futures/market-data/" in policy["aster_direct_snapshot"]["source_urls"]
    assert (
        "https://github.com/asterdex/api-docs/blob/master/V3%28Recommended%29/EN/aster-finance-futures-api-v3.md#order-book"
        in policy["aster_direct_snapshot"]["source_urls"]
    )
    assert "fee tier assumptions" in policy["aster_direct_snapshot"]["blocked_for_production_signal"]
    aster_semantics = policy["aster_direct_snapshot"]["cost_input_semantics"]
    assert aster_semantics["status"] == "diagnostic_metadata_only"
    assert aster_semantics["fee_inputs"]["status"] == "partial_ready_published_defaults_only"
    assert aster_semantics["fee_inputs"]["published_values"]["maker_fee_bps"] == 0.0
    assert aster_semantics["fee_inputs"]["published_values"]["taker_fee_bps"] == 4.0
    assert aster_semantics["depth_inputs"]["status"] == "partial_ready_depth_ladder_display_only"
    assert "fapi/v3/depth.bids" in aster_semantics["depth_inputs"]["source_fields"]
    assert "bid_depth_top_orders_usd" in aster_semantics["depth_inputs"]["source_fields"]
    assert "do not estimate slippage" in aster_semantics["depth_inputs"]["safe_use"]
    assert aster_semantics["slippage_inputs"]["status"] == "not_modeled"
    assert policy["coinglass_perp_dex_enrichment"]["status"] == "research_enrichment"
    assert policy["coinglass_perp_dex_enrichment"]["read_only"] is True
    assert "Aster" in policy["coinglass_perp_dex_enrichment"]["candidate_venues"]
    assert "Hyperliquid" in policy["coinglass_perp_dex_enrichment"]["candidate_venues"]
    assert policy["gmx_formula_validation"]["status"] == "diagnostic_only"
    assert "openInterestLong" in policy["gmx_formula_validation"]["blocked_for_production_signal"]
    assert "availableLiquidityLong" in policy["gmx_formula_validation"]["blocked_for_production_signal"]
    assert "fundingRateLong" in policy["gmx_formula_validation"]["blocked_for_production_signal"]
    assert policy["ui_policy"]["may_show_market_rows"] is True
    assert policy["ui_policy"]["may_rank_by_liquidity"] is False
    assert policy["ui_policy"]["may_submit_orders"] is False
    assert_structured_route_blockers(policy["blockers"], require_scope=True)

    blocker_ids = {blocker["id"] for blocker in policy["blockers"]}
    capability_status = {capability["id"]: capability["status"] for capability in policy["capabilities"]}

    assert "gmx_scale_validation_required" in blocker_ids
    assert "fees_slippage_model_missing" in blocker_ids
    assert "coinglass_enrichment_not_route_input" in blocker_ids
    assert "execution_boundary" in blocker_ids
    blockers_by_id = {blocker["id"]: blocker for blocker in policy["blockers"]}
    assert "liquidity_formula_validation" in blockers_by_id["gmx_scale_validation_required"]["missing_inputs"]
    assert "order_size_usd" in blockers_by_id["fees_slippage_model_missing"]["missing_inputs"]
    assert "display_only_depth" in blockers_by_id["fees_slippage_model_missing"]["blocked_by"]
    assert "do not sum total cost bps" in blockers_by_id["fees_slippage_model_missing"]["safe_use"]
    assert "direct_venue_depth" in blockers_by_id["coinglass_enrichment_not_route_input"]["missing_inputs"]
    assert "connector_write_path" in blockers_by_id["execution_boundary"]["missing_inputs"]
    assert capability_status["direct_market_snapshots"] == "partial_ready"
    assert capability_status["coinglass_perp_dex_enrichment"] == "partial_ready"
    assert capability_status["gmx_token_decimals_diagnostics"] == "partial_ready"
    assert capability_status["gmx_pool_token_amount_diagnostics"] == "partial_ready"
    assert capability_status["gmx_oi_liquidity_usd_diagnostics"] == "partial_ready"
    assert capability_status["route_cost_model_v0"] == "partial_ready"
    assert capability_status["lighter_aster_cost_semantics_metadata"] == "partial_ready"
    assert capability_status["lighter_orderbook_orders_depth_diagnostics"] == "partial_ready"
    assert capability_status["aster_depth_ladder_diagnostics"] == "partial_ready"
    assert capability_status["aster_fee_schedule_metadata"] == "partial_ready"
    assert capability_status["gmx_rate_semantics_metadata"] == "partial_ready"
    assert capability_status["gmx_rate_relation_fixtures"] == "partial_ready"
    assert capability_status["multi_venue_liquidity_ranking"] == "blocked"
    assert capability_status["route_level_pricing"] == "blocked"
    assert capability_status["execution"] == "blocked"

    confirmed = {
        item["field_group"]: item["status"]
        for item in policy["gmx_formula_validation"]["confirmed_for_diagnostics"]
    }
    assert confirmed["poolAmountLong/poolAmountShort"] == "token_amount_units"
    assert confirmed["Precision factors"] == "float_precision_confirmed"
    assert confirmed["openInterest vs openInterestInTokens"] == "separate_contract_paths_confirmed"
    assert confirmed["openInterest*/availableLiquidity*"] == "gmx_api_ticker_usd_decimals_confirmed"
    assert (
        confirmed["fundingRate*/borrowingRate*/netRate*"]
        == "gmx_market_ticker_hourly_rate_semantics_guardrail_added"
    )


def test_perp_dex_route_model_is_read_only_inputs_required() -> None:
    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/route-model")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is False
    assert payload["meta"]["source"] == "deltagrid_perp_dex_route_model"

    model = payload["data"]
    assert model["version"] == "v0"
    assert model["status"] == "inputs_required"
    assert model["read_only"] is True
    assert model["execution_enabled"] is False
    assert model["ranking_enabled"] is False
    assert model["production_signal_enabled"] is False
    assert model["supported_venues"] == ["hyperliquid", "dydx", "lighter", "aster", "gmx"]
    assert model["third_party_enrichment_sources"] == ["coinglass_futures_coins_markets"]
    assert model["output_policy"]["may_show_checklist"] is True
    assert model["output_policy"]["may_show_formula_skeleton"] is True
    assert model["output_policy"]["may_show_diagnostic_cost_components"] is True
    assert model["output_policy"]["may_estimate_cost_bps"] is False
    assert model["output_policy"]["may_rank_routes"] is False
    assert model["output_policy"]["may_submit_orders"] is False
    assert_structured_route_blockers(model["blockers"])

    component_status = {component["id"]: component["status"] for component in model["model_components"]}
    assert component_status["price_source"] == "partial_ready"
    assert component_status["trading_fee"] == "input_required"
    assert component_status["slippage_price_impact"] == "input_required"
    assert component_status["funding_borrow_carry"] == "input_required"
    assert component_status["execution_boundary"] == "blocked"

    readiness_status = {venue["venue_id"]: venue["status"] for venue in model["venue_readiness"]}
    readiness = {venue["venue_id"]: venue for venue in model["venue_readiness"]}
    assert readiness_status["hyperliquid"] == "partial_ready"
    assert readiness_status["dydx"] == "partial_ready"
    assert readiness_status["lighter"] == "partial_ready"
    assert readiness_status["aster"] == "partial_ready"
    assert readiness_status["gmx"] == "diagnostic_only"
    assert readiness_status["coinglass_perp_dex"] == "research_enrichment"
    assert readiness["lighter"]["cost_input_status"]["fees"] == "partial_ready_display_only"
    assert readiness["lighter"]["cost_input_status"]["depth"] == "partial_ready_top_orders_only"
    assert "top resting order depth" in readiness["lighter"]["source_semantics"]
    assert "top_of_book_spread_bps" in readiness["lighter"]["available_inputs"]
    assert "bid_depth_top_orders_usd" in readiness["lighter"]["available_inputs"]
    assert "depth_aggregation_policy" in readiness["lighter"]["missing_inputs"]
    assert readiness["aster"]["cost_input_status"]["fees"] == "partial_ready_published_defaults_only"
    assert readiness["aster"]["cost_input_status"]["depth"] == "partial_ready_depth_ladder_display_only"
    assert "published_usdt_perp_fee_schedule" in readiness["aster"]["available_inputs"]
    assert "top_of_book_spread_bps" in readiness["aster"]["available_inputs"]
    assert "bid_depth_top_orders_usd" in readiness["aster"]["available_inputs"]
    assert "depth_aggregation_policy" in readiness["aster"]["missing_inputs"]
    assert "public depth ladder" in readiness["aster"]["source_semantics"]

    required_inputs = {item["id"] for item in model["required_inputs"]}
    assert_structured_route_required_inputs(model["required_inputs"])
    assert "venue_fee_schedule" in required_inputs
    assert "order_intent" in required_inputs
    assert "depth_or_impact_model" in required_inputs
    assert "carry_horizon" in required_inputs
    assert "risk_limits" in required_inputs

    formulas = model["formula_skeleton"]
    assert_route_formula_skeleton(formulas)
    assert formulas["gross_edge_bps"] == "expected_exit_price_bps - expected_entry_price_bps"
    assert "estimated_cost_bps" in formulas
    assert "route_allowed" in formulas
    diagnostics = model["diagnostic_cost_estimate_v0"]
    assert_structured_route_cost_diagnostics(diagnostics)
    diagnostic_components = {component["id"]: component for component in diagnostics["components"]}
    diagnostic_components_list = diagnostics["components"]
    required_input_breakdown = diagnostics["summary"]["required_input_breakdown"]
    assert [item["input_id"] for item in required_input_breakdown] == [
        item["id"] for item in model["required_inputs"]
    ]
    components_by_required_input: dict[str, list[dict]] = {}
    for component in diagnostic_components_list:
        for input_id in component["required_input_ids"]:
            components_by_required_input.setdefault(input_id, []).append(component)
    for input_row in required_input_breakdown:
        input_components = components_by_required_input.get(input_row["input_id"], [])
        venue_ids = []
        for component in input_components:
            if component["venue_id"] not in venue_ids:
                venue_ids.append(component["venue_id"])
        assert input_row["input_label"]
        assert input_row["reason"]
        assert input_row["component_count"] == len(input_components)
        assert input_row["component_ids"] == [component["id"] for component in input_components]
        assert input_row["venue_ids"] == venue_ids
        assert input_row["display_component_ids"] == [
            component["id"] for component in input_components if component["may_emit_component_bps"]
        ]
        assert input_row["blocked_numeric_component_ids"] == [
            component["id"] for component in input_components if not component["may_emit_component_bps"]
        ]
        assert input_row["sourced_component_ids"] == [
            component["id"] for component in input_components if component["source_fields"]
        ]
        assert input_row["numeric_total_status"] == "blocked"
        assert input_row["safe_use"]
        assert input_row["next_action"]
    assert required_input_breakdown[-1]["input_id"] == "risk_limits"
    assert required_input_breakdown[-1]["status"] == "route_gate_only"
    assert required_input_breakdown[-1]["component_count"] == 0

    source_field_breakdown = diagnostics["summary"]["source_field_breakdown"]
    components_by_source_field: dict[str, list[dict]] = {}
    for component in diagnostic_components_list:
        for source_field in component["source_fields"]:
            components_by_source_field.setdefault(source_field, []).append(component)
    assert [item["source_field"] for item in source_field_breakdown] == list(components_by_source_field)
    for source_row in source_field_breakdown:
        source_components = components_by_source_field[source_row["source_field"]]
        venue_ids = []
        required_input_ids = []
        for component in source_components:
            if component["venue_id"] not in venue_ids:
                venue_ids.append(component["venue_id"])
            for input_id in component["required_input_ids"]:
                if input_id not in required_input_ids:
                    required_input_ids.append(input_id)
        assert source_row["status"] == "display_context_only"
        assert source_row["component_count"] == len(source_components)
        assert source_row["component_ids"] == [component["id"] for component in source_components]
        assert source_row["venue_ids"] == venue_ids
        assert source_row["required_input_ids"] == required_input_ids
        assert source_row["display_component_ids"] == [
            component["id"] for component in source_components if component["may_emit_component_bps"]
        ]
        assert source_row["blocked_numeric_component_ids"] == [
            component["id"] for component in source_components if not component["may_emit_component_bps"]
        ]
        assert source_row["numeric_total_status"] == "blocked"
        assert source_row["safe_use"]

    safe_use_breakdown = diagnostics["summary"]["safe_use_breakdown"]
    components_by_safe_use: dict[str, list[dict]] = {}
    for component in diagnostic_components_list:
        components_by_safe_use.setdefault(component["safe_use"], []).append(component)
    assert [item["safe_use"] for item in safe_use_breakdown] == list(components_by_safe_use)
    for safe_use_row in safe_use_breakdown:
        safe_use_components = components_by_safe_use[safe_use_row["safe_use"]]
        venue_ids = []
        required_input_ids = []
        for component in safe_use_components:
            if component["venue_id"] not in venue_ids:
                venue_ids.append(component["venue_id"])
            for input_id in component["required_input_ids"]:
                if input_id not in required_input_ids:
                    required_input_ids.append(input_id)
        assert safe_use_row["status"] == "boundary_notice"
        assert safe_use_row["component_count"] == len(safe_use_components)
        assert safe_use_row["component_ids"] == [component["id"] for component in safe_use_components]
        assert safe_use_row["venue_ids"] == venue_ids
        assert safe_use_row["required_input_ids"] == required_input_ids
        assert safe_use_row["display_component_ids"] == [
            component["id"] for component in safe_use_components if component["may_emit_component_bps"]
        ]
        assert safe_use_row["blocked_numeric_component_ids"] == [
            component["id"] for component in safe_use_components if not component["may_emit_component_bps"]
        ]
        assert safe_use_row["numeric_total_status"] == "blocked"
        assert safe_use_row["next_action"]

    readiness_rollup = diagnostics["summary"]["readiness_rollup"]
    assert [item["category_id"] for item in readiness_rollup] == ["fees", "depth_slippage", "carry", "risk_limits"]
    rollup_by_id = {item["category_id"]: item for item in readiness_rollup}
    assert rollup_by_id["fees"]["status"] == "partial_ready_display_only"
    assert rollup_by_id["fees"]["component_count"] == 2
    assert rollup_by_id["depth_slippage"]["status"] == "partial_ready_display_only"
    assert rollup_by_id["depth_slippage"]["component_count"] == 4
    assert rollup_by_id["carry"]["status"] == "partial_ready_display_only"
    assert rollup_by_id["carry"]["component_count"] == 1
    assert rollup_by_id["risk_limits"]["status"] == "route_gate_only"
    assert rollup_by_id["risk_limits"]["component_count"] == 0
    for rollup in readiness_rollup:
        assert rollup["required_input_ids"]
        assert rollup["numeric_total_status"] == "blocked"
        assert rollup["safe_use"]
        assert rollup["next_action"]

    depth_policy = diagnostics["summary"]["depth_staleness_policy_checklist"]
    assert [item["policy_id"] for item in depth_policy] == [
        "lighter_top_order_depth_staleness",
        "aster_top_of_book_staleness",
        "aster_depth_ladder_staleness",
    ]
    assert [item["component_id"] for item in depth_policy] == [
        "lighter_top_order_depth",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
    ]
    required_depth_policy_inputs = [
        "depth_snapshot_timestamp",
        "max_depth_age_ms",
        "stale_depth_action",
        "order_size_usd",
        "side",
        "depth_aggregation_policy",
        "liquidity_cap",
    ]
    for policy in depth_policy:
        component = diagnostic_components[policy["component_id"]]
        assert policy["status"] == "staleness_policy_required"
        assert policy["source_fields"] == component["source_fields"]
        assert policy["required_policy_inputs"] == required_depth_policy_inputs
        assert policy["blocked_by"] == [
            "no_depth_snapshot_timestamp",
            "no_max_depth_age_ms",
            "no_stale_depth_action",
            "no_order_size_context",
        ]
        assert policy["may_emit_slippage_bps"] is False
        assert policy["numeric_total_status"] == "blocked"
        assert "do not estimate slippage" in policy["safe_use"]
        assert policy["next_action"]

    required_policy_inputs = diagnostics["summary"]["required_policy_input_breakdown"]
    assert [item["input_id"] for item in required_policy_inputs] == required_depth_policy_inputs
    for policy_input in required_policy_inputs:
        assert policy_input["status"] == "policy_input_required"
        assert policy_input["policy_count"] == len(depth_policy)
        assert policy_input["policy_ids"] == [item["policy_id"] for item in depth_policy]
        assert policy_input["component_ids"] == [
            "lighter_top_order_depth",
            "aster_top_of_book_spread",
            "aster_depth_ladder",
        ]
        assert policy_input["venue_ids"] == ["lighter", "aster"]
        assert policy_input["source_endpoints"] == ["orderBookOrders", "ticker/bookTicker", "fapi/v3/depth"]
        assert policy_input["blocked_by"] == [
            "no_depth_snapshot_timestamp",
            "no_max_depth_age_ms",
            "no_stale_depth_action",
            "no_order_size_context",
        ]
        assert policy_input["may_emit_slippage_bps"] is False
        assert policy_input["numeric_total_status"] == "blocked"
        assert "do not estimate slippage" in policy_input["safe_use"]
        assert policy_input["next_action"]

    next_action_breakdown = diagnostics["summary"]["next_action_breakdown"]
    expected_actions = []
    for row in diagnostics["summary"]["required_input_breakdown"]:
        if row["next_action"] not in expected_actions:
            expected_actions.append(row["next_action"])
    for row in readiness_rollup:
        if row["next_action"] not in expected_actions:
            expected_actions.append(row["next_action"])
    for row in depth_policy:
        if row["next_action"] not in expected_actions:
            expected_actions.append(row["next_action"])
    assert [item["next_action"] for item in next_action_breakdown] == expected_actions
    for index, action in enumerate(next_action_breakdown, start=1):
        assert action["action_id"] == f"next_action_{index}"
        assert action["status"] == "action_required"
        assert action["source_count"] >= 1
        assert action["source_types"]
        assert action["source_ids"]
        assert action["numeric_total_status"] == "blocked"
        assert "do not estimate route cost" in action["safe_use"]
    depth_action = next(
        item
        for item in next_action_breakdown
        if item["next_action"] == "add timestamp freshness, stale-depth policy and order-size aggregation before Lighter slippage bps"
    )
    assert depth_action["source_types"] == ["depth_staleness_policy"]
    assert depth_action["source_ids"] == ["lighter_top_order_depth_staleness"]
    assert depth_action["required_policy_inputs"] == required_depth_policy_inputs
    assert depth_action["component_ids"] == ["lighter_top_order_depth"]
    assert depth_action["venue_ids"] == ["lighter"]
    assert depth_action["policy_ids"] == ["lighter_top_order_depth_staleness"]

    source_input_action_coverage = diagnostics["summary"]["source_input_action_coverage"]
    assert [item["source_field"] for item in source_input_action_coverage] == list(components_by_source_field)
    for index, coverage_row in enumerate(source_input_action_coverage, start=1):
        source_components = components_by_source_field[coverage_row["source_field"]]
        component_ids = [component["id"] for component in source_components]
        venue_ids = []
        required_input_ids = []
        for component in source_components:
            if component["venue_id"] not in venue_ids:
                venue_ids.append(component["venue_id"])
            for input_id in component["required_input_ids"]:
                if input_id not in required_input_ids:
                    required_input_ids.append(input_id)
        matched_actions = [
            action
            for action in next_action_breakdown
            if any(input_id in action["required_input_ids"] for input_id in required_input_ids)
            or any(component_id in action["component_ids"] for component_id in component_ids)
        ]
        source_types = []
        for action in matched_actions:
            for source_type in action["source_types"]:
                if source_type not in source_types:
                    source_types.append(source_type)
        assert coverage_row["coverage_id"] == f"source_field_{index}"
        assert coverage_row["status"] == "display_context_only"
        assert coverage_row["component_count"] == len(source_components)
        assert coverage_row["component_ids"] == component_ids
        assert coverage_row["venue_ids"] == venue_ids
        assert coverage_row["required_input_count"] == len(required_input_ids)
        assert coverage_row["required_input_ids"] == required_input_ids
        assert coverage_row["next_action_count"] == len(matched_actions)
        assert coverage_row["next_action_ids"] == [action["action_id"] for action in matched_actions]
        assert coverage_row["next_actions"] == [action["next_action"] for action in matched_actions]
        assert coverage_row["source_types"] == source_types
        assert coverage_row["display_component_ids"] == [
            component["id"] for component in source_components if component["may_emit_component_bps"]
        ]
        assert coverage_row["blocked_numeric_component_ids"] == [
            component["id"] for component in source_components if not component["may_emit_component_bps"]
        ]
        assert coverage_row["numeric_total_status"] == "blocked"
        assert "do not close route-ready inputs" in coverage_row["safe_use"]
        assert coverage_row["next_action"]

    def source_fields_for_components(component_ids: list[str]) -> list[str]:
        source_fields = []
        for source_field, source_components in components_by_source_field.items():
            if any(component["id"] in component_ids for component in source_components):
                source_fields.append(source_field)
        return source_fields

    route_ready_evidence = diagnostics["summary"]["route_ready_evidence_checklist"]
    expected_evidence = [
        {
            "gate_id": "fee_schedule_evidence",
            "gate_label": "Fee Schedule Evidence",
            "required_input_ids": ["venue_fee_schedule"],
            "required_policy_inputs": [],
            "component_ids": ["lighter_fee_fields", "aster_published_fee_schedule"],
            "policy_ids": [],
            "blocked_outputs": ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"],
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
            "policy_ids": [item["policy_id"] for item in depth_policy],
            "blocked_outputs": ["fee_bps", "slippage_bps", "carry_bps", "estimated_cost_bps", "route_allowed"],
        },
        {
            "gate_id": "depth_freshness_evidence",
            "gate_label": "Depth Freshness Evidence",
            "required_input_ids": ["depth_or_impact_model"],
            "required_policy_inputs": ["depth_snapshot_timestamp", "max_depth_age_ms", "stale_depth_action"],
            "component_ids": ["lighter_top_order_depth", "aster_top_of_book_spread", "aster_depth_ladder"],
            "policy_ids": [item["policy_id"] for item in depth_policy],
            "blocked_outputs": ["slippage_bps", "estimated_cost_bps", "route_allowed"],
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
            "policy_ids": [item["policy_id"] for item in depth_policy],
            "blocked_outputs": ["slippage_bps", "estimated_cost_bps", "route_allowed"],
        },
        {
            "gate_id": "carry_semantics_evidence",
            "gate_label": "Carry Semantics Evidence",
            "required_input_ids": ["carry_horizon"],
            "required_policy_inputs": [],
            "component_ids": ["funding_borrow_carry"],
            "policy_ids": [],
            "blocked_outputs": ["carry_bps", "estimated_cost_bps", "net_edge_bps"],
        },
        {
            "gate_id": "risk_limits_evidence",
            "gate_label": "Risk Limits Evidence",
            "required_input_ids": ["risk_limits"],
            "required_policy_inputs": [],
            "component_ids": [],
            "policy_ids": [],
            "blocked_outputs": ["route_allowed", "may_submit_orders"],
        },
    ]
    assert [item["gate_id"] for item in route_ready_evidence] == [
        item["gate_id"] for item in expected_evidence
    ]
    for evidence_row, expected in zip(route_ready_evidence, expected_evidence, strict=True):
        expected_source_fields = source_fields_for_components(expected["component_ids"])
        assert evidence_row["gate_label"] == expected["gate_label"]
        assert evidence_row["status"] == "evidence_required"
        assert evidence_row["required_input_ids"] == expected["required_input_ids"]
        assert evidence_row["required_policy_inputs"] == expected["required_policy_inputs"]
        assert evidence_row["component_ids"] == expected["component_ids"]
        assert evidence_row["policy_ids"] == expected["policy_ids"]
        assert evidence_row["source_field_ids"] == expected_source_fields
        assert evidence_row["blocked_outputs"] == expected["blocked_outputs"]
        assert evidence_row["evidence_count"] == len(expected_source_fields)
        assert evidence_row["numeric_total_status"] == "blocked"
        assert evidence_row["may_estimate_cost_bps"] is False
        assert evidence_row["may_rank_routes"] is False
        assert evidence_row["may_submit_orders"] is False
        assert "do not estimate route cost" in evidence_row["safe_use"]
        assert evidence_row["next_action"]

    evidence_by_gate_id = {item["gate_id"]: item for item in route_ready_evidence}

    def evidence_values(gate_ids: list[str], key: str) -> list[str]:
        values = []
        for gate_id in gate_ids:
            for value in evidence_by_gate_id[gate_id][key]:
                if value not in values:
                    values.append(value)
        return values

    gmx_rate_semantics_for_evidence = model["gmx_rate_semantics"]
    gmx_mapping_review_for_evidence = gmx_rate_semantics_for_evidence["mapping_review"]
    expected_venue_evidence = [
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
            "diagnostic_field_ids": gmx_mapping_review_for_evidence["diagnostic_fields"],
            "fixture_coverage_ids": [item["id"] for item in gmx_rate_semantics_for_evidence["fixture_coverage"]],
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
        },
    ]
    venue_evidence_status = diagnostics["summary"]["venue_evidence_status"]
    assert [item["venue_id"] for item in venue_evidence_status] == [
        item["venue_id"] for item in expected_venue_evidence
    ]
    for venue_row, expected in zip(venue_evidence_status, expected_venue_evidence, strict=True):
        gate_ids = expected["venue_gate_ids"] + expected["cross_venue_gate_ids"]
        route_ready_gate_ids = [gate_id for gate_id in gate_ids if gate_id in evidence_by_gate_id]
        expected_required_inputs = evidence_values(route_ready_gate_ids, "required_input_ids")
        expected_policy_inputs = evidence_values(route_ready_gate_ids, "required_policy_inputs")
        expected_blocked_outputs = evidence_values(route_ready_gate_ids, "blocked_outputs")
        if expected["venue_id"] == "gmx":
            for value in ["order_intent", "carry_horizon", "risk_limits"]:
                if value not in expected_required_inputs:
                    expected_required_inputs.append(value)
            for value in ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"]:
                if value not in expected_blocked_outputs:
                    expected_blocked_outputs.append(value)
        expected_source_fields = source_fields_for_components(expected["component_ids"])
        assert venue_row["venue_label"] == expected["venue_label"]
        assert venue_row["venue_scope"] == expected["venue_scope"]
        assert venue_row["status"] == expected["status"]
        assert venue_row["venue_gate_ids"] == expected["venue_gate_ids"]
        assert venue_row["cross_venue_gate_ids"] == expected["cross_venue_gate_ids"]
        assert venue_row["required_input_ids"] == expected_required_inputs
        assert venue_row["required_policy_inputs"] == expected_policy_inputs
        assert venue_row["component_ids"] == expected["component_ids"]
        assert venue_row["policy_ids"] == expected["policy_ids"]
        assert venue_row["source_field_ids"] == expected_source_fields
        assert venue_row["diagnostic_field_ids"] == expected["diagnostic_field_ids"]
        assert venue_row["fixture_coverage_ids"] == expected["fixture_coverage_ids"]
        assert venue_row["blocked_outputs"] == expected_blocked_outputs
        assert venue_row["evidence_count"] == (
            len(expected_source_fields)
            + len(expected["diagnostic_field_ids"])
            + len(expected["fixture_coverage_ids"])
        )
        assert venue_row["numeric_total_status"] == "blocked"
        assert venue_row["may_estimate_cost_bps"] is False
        assert venue_row["may_rank_routes"] is False
        assert venue_row["may_submit_orders"] is False
        assert "do not estimate route cost" in venue_row["safe_use"]
        assert venue_row["next_action"]

    assert diagnostic_components["lighter_fee_fields"]["status"] == "source_fields_available_unit_unconfirmed"
    assert diagnostic_components["lighter_fee_fields"]["may_emit_component_bps"] is False
    assert diagnostic_components["lighter_top_order_depth"]["status"] == "partial_ready_display_only"
    assert diagnostic_components["lighter_top_order_depth"]["may_emit_component_bps"] is True
    assert "bid_depth_top_orders_usd" in diagnostic_components["lighter_top_order_depth"]["source_fields"]
    assert "do not treat as executable slippage" in diagnostic_components["lighter_top_order_depth"]["safe_use"]
    assert diagnostic_components["aster_published_fee_schedule"]["published_values"]["taker_fee_bps"] == 4.0
    assert diagnostic_components["aster_published_fee_schedule"]["may_emit_component_bps"] is False
    assert diagnostic_components["aster_top_of_book_spread"]["may_emit_component_bps"] is True
    assert "display spread only" in diagnostic_components["aster_top_of_book_spread"]["safe_use"]
    assert diagnostic_components["aster_depth_ladder"]["status"] == "partial_ready_display_only"
    assert diagnostic_components["aster_depth_ladder"]["may_emit_component_bps"] is True
    assert "bid_depth_top_orders_usd" in diagnostic_components["aster_depth_ladder"]["source_fields"]
    assert "do not treat as executable slippage" in diagnostic_components["aster_depth_ladder"]["safe_use"]
    assert diagnostic_components["slippage_price_impact"]["status"] == "input_required"

    gmx_rate_semantics = model["gmx_rate_semantics"]
    assert gmx_rate_semantics["status"] == "guardrail_metadata_only"
    assert "https://github.com/gmx-io/gmx-interface/blob/master/sdk/src/utils/fees/index.ts" in gmx_rate_semantics["source_urls"]
    assert "https://github.com/gmx-io/gmx-synthetics/blob/main/contracts/reader/ReaderUtils.sol" in gmx_rate_semantics["source_urls"]

    gmx_confirmed = {item["field_group"]: item["status"] for item in gmx_rate_semantics["confirmed_for_modeling"]}
    assert gmx_confirmed["MarketTicker rates"] == "fields_present"
    assert gmx_confirmed["ticker period"] == "hourly_period_confirmed"
    assert gmx_confirmed["net rate relation"] == "source_relation_guardrail_added"
    assert gmx_confirmed["funding sign convention"] == "requires_fixture_mapping"
    assert gmx_confirmed["borrowing fee relation"] == "requires_position_context"
    assert gmx_rate_semantics["mapping_review"]["status"] == "source_vs_live_mapping_unresolved"
    assert "rate_relation_summary" in gmx_rate_semantics["mapping_review"]["diagnostic_fields"]
    assert "rate_source_fields_status" in gmx_rate_semantics["mapping_review"]["diagnostic_fields"]
    assert "fundingFactorPerSecond" in gmx_rate_semantics["mapping_review"]["source_inputs_required"]
    assert "mapping evidence only" in gmx_rate_semantics["mapping_review"]["safe_use"]
    fixture_coverage = {
        item["id"]: item["status"]
        for item in gmx_rate_semantics["fixture_coverage"]
    }
    assert fixture_coverage["net_rate_relation_raw_fields"] == "offline_guardrail_added"
    assert fixture_coverage["live_nonzero_borrowing_raw_sum_relation_observed"] == "live_smoke_observed"
    assert fixture_coverage["live_zero_borrowing_relation_ambiguity"] == "live_smoke_observed"
    assert fixture_coverage["live_shape_offline_fixture"] == "offline_guardrail_added"
    assert "live /markets/info source helper inputs unavailable" in gmx_rate_semantics["blocked_for_numeric_carry"]
    assert "live /markets/info nonzero borrowing rate mapping review" in gmx_rate_semantics["blocked_for_numeric_carry"]
    assert "broader live fixture coverage across market states" in gmx_rate_semantics["blocked_for_numeric_carry"]
    assert "holding_period_hours input" in gmx_rate_semantics["blocked_for_numeric_carry"]
    assert "position_notional_usd input" in gmx_rate_semantics["blocked_for_numeric_carry"]

    gmx_rate_mapping_review = model["gmx_rate_mapping_review_v0"]
    assert gmx_rate_mapping_review["status"] == "mapping_review_required"
    assert gmx_rate_mapping_review["read_only"] is True
    assert gmx_rate_mapping_review["source_relation_status"] == "source_relation_guardrail_added"
    assert gmx_rate_mapping_review["live_mapping_status"] == "source_vs_live_mapping_unresolved"
    assert gmx_rate_mapping_review["source_confirmed_count"] == len(gmx_rate_semantics["mapping_review"]["source_confirmed"])
    assert gmx_rate_mapping_review["live_observed_count"] == len(gmx_rate_semantics["mapping_review"]["live_observed"])
    assert gmx_rate_mapping_review["fixture_coverage_count"] == len(gmx_rate_semantics["fixture_coverage"])
    assert gmx_rate_mapping_review["diagnostic_field_ids"] == gmx_rate_semantics["mapping_review"]["diagnostic_fields"]
    assert gmx_rate_mapping_review["source_inputs_required"] == gmx_rate_semantics["mapping_review"]["source_inputs_required"]
    assert gmx_rate_mapping_review["fixture_coverage_ids"] == [item["id"] for item in gmx_rate_semantics["fixture_coverage"]]
    assert gmx_rate_mapping_review["blocked_outputs"] == [
        "carry_bps",
        "estimated_cost_bps",
        "net_edge_bps",
        "route_allowed",
    ]
    assert gmx_rate_mapping_review["may_emit_carry_bps"] is False
    assert gmx_rate_mapping_review["may_estimate_cost_bps"] is False
    assert gmx_rate_mapping_review["may_rank_routes"] is False
    assert gmx_rate_mapping_review["may_submit_orders"] is False
    assert "no percent, bps" in gmx_rate_mapping_review["safe_use"]
    assert gmx_rate_mapping_review["next_action"] == gmx_rate_semantics["next_action"]
    assert [item["review_id"] for item in gmx_rate_mapping_review["review_items"]] == [
        "source_relation_guardrail",
        "live_nonzero_borrowing_mapping",
        "source_helper_inputs",
        "carry_conversion_boundary",
    ]
    for review_item in gmx_rate_mapping_review["review_items"]:
        assert review_item["diagnostic_field_ids"]
        assert review_item["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert "no percent, bps" in review_item["safe_use"]
        assert review_item["next_action"]
    assert gmx_rate_mapping_review["review_items"][0]["status"] == "source_relation_guardrail_added"
    assert gmx_rate_mapping_review["review_items"][1]["status"] == "mapping_review_required"
    assert gmx_rate_mapping_review["review_items"][2]["status"] == "source_inputs_missing"
    assert gmx_rate_mapping_review["review_items"][3]["status"] == "blocked_for_carry_conversion"
    assert [item["blocker_id"] for item in gmx_rate_mapping_review["blocker_breakdown"]] == [
        "live_markets_info_nonzero_borrowing_rate_mapping_review",
        "broader_live_fixture_coverage_across_market_states",
        "live_markets_info_source_helper_inputs_unavailable",
        "side_aware_funding_sign_tests",
        "holding_period_hours_input",
        "position_notional_usd_input",
        "production_decision_on_hourly_vs_annualized_display",
    ]
    gmx_mapping_blockers = {
        item["blocker_id"]: item
        for item in gmx_rate_mapping_review["blocker_breakdown"]
    }
    assert gmx_mapping_blockers["live_markets_info_nonzero_borrowing_rate_mapping_review"]["review_ids"] == [
        "source_relation_guardrail",
        "live_nonzero_borrowing_mapping",
        "carry_conversion_boundary",
    ]
    assert gmx_mapping_blockers["live_markets_info_source_helper_inputs_unavailable"]["review_ids"] == [
        "source_helper_inputs",
        "carry_conversion_boundary",
    ]
    for blocker in gmx_rate_mapping_review["blocker_breakdown"]:
        assert blocker["review_count"] == len(blocker["review_ids"])
        assert blocker["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert blocker["may_emit_carry_bps"] is False
        assert blocker["may_estimate_cost_bps"] is False
        assert blocker["may_rank_routes"] is False
        assert blocker["may_submit_orders"] is False
        assert "no percent, bps" in blocker["safe_use"]
        assert blocker["next_action"]
    assert [item["case_id"] for item in gmx_rate_mapping_review["fixture_readiness_matrix"]] == [
        "source_relation_raw_fields",
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
        "source_helper_inputs_presence",
    ]
    gmx_fixture_cases = {
        item["case_id"]: item
        for item in gmx_rate_mapping_review["fixture_readiness_matrix"]
    }
    assert gmx_fixture_cases["source_relation_raw_fields"]["status"] == "offline_guardrail_added"
    assert gmx_fixture_cases["live_nonzero_borrowing_relation"]["status"] == "mapping_review_required"
    assert gmx_fixture_cases["live_zero_borrowing_ambiguity"]["status"] == "relation_ambiguous"
    assert gmx_fixture_cases["longs_pay_shorts_direction"]["status"] == "fixture_required"
    assert gmx_fixture_cases["source_helper_inputs_presence"]["status"] == "source_inputs_missing"
    assert gmx_fixture_cases["live_nonzero_borrowing_relation"]["evidence_count"] == 2
    assert gmx_fixture_cases["longs_pay_shorts_direction"]["evidence_count"] == 0
    assert "longsPayShorts" in gmx_fixture_cases["longs_pay_shorts_direction"]["source_inputs_required"]
    expected_gmx_side_expectation_ids = [
        "long_position_pays_when_longs_pay_shorts_true",
        "short_position_receives_when_longs_pay_shorts_true",
        "short_position_pays_when_longs_pay_shorts_false",
        "long_position_receives_when_longs_pay_shorts_false",
    ]
    assert gmx_fixture_cases["longs_pay_shorts_direction"]["expectation_ids"] == expected_gmx_side_expectation_ids
    assert len(gmx_fixture_cases["longs_pay_shorts_direction"]["expectation_notes"]) == 4
    for fixture_case in gmx_rate_mapping_review["fixture_readiness_matrix"]:
        assert fixture_case["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert fixture_case["may_emit_carry_bps"] is False
        assert "no percent, bps" in fixture_case["safe_use"]
        assert fixture_case["next_action"]
    assert [item["expectation_id"] for item in gmx_rate_mapping_review["side_aware_fixture_expectations"]] == expected_gmx_side_expectation_ids
    expected_side_expectations = [
        ("long", True, "pay"),
        ("short", True, "receive"),
        ("short", False, "pay"),
        ("long", False, "receive"),
    ]
    for expectation, expected in zip(gmx_rate_mapping_review["side_aware_fixture_expectations"], expected_side_expectations):
        expected_side, expected_longs_pay_shorts, expected_direction = expected
        assert expectation["case_id"] == "longs_pay_shorts_direction"
        assert expectation["status"] == "fixture_required"
        assert expectation["position_side"] == expected_side
        assert expectation["longs_pay_shorts"] is expected_longs_pay_shorts
        assert expectation["expected_funding_direction"] == expected_direction
        assert expectation["required_source_inputs"] == ["fundingFactorPerSecond", "longsPayShorts"]
        assert expectation["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert expectation["may_emit_carry_bps"] is False
        assert "no percent, bps" in expectation["safe_use"]
    assert [item["check_id"] for item in gmx_rate_mapping_review["mapping_decision_checklist"]] == [
        "source_helper_inputs_available",
        "nonzero_borrowing_relation_reviewed",
        "side_aware_direction_fixtures",
        "carry_inputs_defined",
        "display_unit_decision_recorded",
    ]
    gmx_decision_checks = {
        item["check_id"]: item
        for item in gmx_rate_mapping_review["mapping_decision_checklist"]
    }
    assert gmx_decision_checks["source_helper_inputs_available"]["status"] == "source_inputs_missing"
    assert gmx_decision_checks["nonzero_borrowing_relation_reviewed"]["status"] == "mapping_review_required"
    assert gmx_decision_checks["side_aware_direction_fixtures"]["status"] == "fixture_required"
    assert gmx_decision_checks["carry_inputs_defined"]["status"] == "input_required"
    assert gmx_decision_checks["display_unit_decision_recorded"]["status"] == "policy_input_required"
    assert gmx_decision_checks["side_aware_direction_fixtures"]["required_expectation_ids"] == expected_gmx_side_expectation_ids
    assert [item["manual_approval_id"] for item in gmx_rate_mapping_review["mapping_decision_checklist"]] == [
        "gmx_source_helper_input_review",
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_side_aware_sign_review",
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    for check in gmx_rate_mapping_review["mapping_decision_checklist"]:
        assert check["manual_approval_required"] is True
        assert check["manual_approval_id"]
        assert check["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert check["may_emit_carry_bps"] is False
        assert check["may_estimate_cost_bps"] is False
        assert check["may_rank_routes"] is False
        assert check["may_submit_orders"] is False
        assert "no percent, bps" in check["safe_use"]
        assert check["next_action"]
    gmx_carry_summary = gmx_rate_mapping_review["carry_readiness_summary"]
    assert gmx_carry_summary["status"] == "blocked_for_diagnostic_carry_bps"
    assert gmx_carry_summary["input_count"] == 5
    assert gmx_carry_summary["blocked_input_count"] == 5
    assert gmx_carry_summary["manual_approval_count"] == 5
    assert sorted(gmx_carry_summary["required_source_inputs"]) == sorted(
        gmx_rate_mapping_review["source_inputs_required"]
    )
    assert gmx_carry_summary["required_fixture_case_ids"] == [
        "source_relation_raw_fields",
        "longs_pay_shorts_direction",
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "source_helper_inputs_presence",
    ]
    assert gmx_carry_summary["required_expectation_ids"] == expected_gmx_side_expectation_ids
    assert sorted(gmx_carry_summary["required_decision_check_ids"]) == sorted(
        [item["check_id"] for item in gmx_rate_mapping_review["mapping_decision_checklist"]]
    )
    assert gmx_carry_summary["required_manual_approval_ids"] == [
        "gmx_source_helper_input_review",
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_side_aware_sign_review",
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    assert gmx_carry_summary["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
    assert gmx_carry_summary["may_emit_carry_bps"] is False
    assert gmx_carry_summary["may_estimate_cost_bps"] is False
    assert gmx_carry_summary["may_rank_routes"] is False
    assert gmx_carry_summary["may_submit_orders"] is False
    assert "no percent, bps" in gmx_carry_summary["safe_use"]
    assert gmx_carry_summary["next_action"]
    assert [item["input_id"] for item in gmx_rate_mapping_review["carry_input_checklist"]] == [
        "holding_period_hours",
        "position_notional_usd",
        "rate_sign_convention",
        "source_helper_inputs",
        "display_unit_decision",
    ]
    gmx_carry_inputs = {
        item["input_id"]: item
        for item in gmx_rate_mapping_review["carry_input_checklist"]
    }
    assert gmx_carry_inputs["holding_period_hours"]["status"] == "input_required"
    assert gmx_carry_inputs["position_notional_usd"]["status"] == "input_required"
    assert gmx_carry_inputs["rate_sign_convention"]["status"] == "fixture_required"
    assert gmx_carry_inputs["source_helper_inputs"]["status"] == "source_inputs_missing"
    assert gmx_carry_inputs["display_unit_decision"]["status"] == "policy_input_required"
    assert gmx_carry_inputs["rate_sign_convention"]["required_expectation_ids"] == expected_gmx_side_expectation_ids
    assert "side_aware_direction_fixtures" in gmx_carry_inputs["rate_sign_convention"]["required_decision_check_ids"]
    assert gmx_carry_inputs["source_helper_inputs"]["required_source_inputs"] == gmx_rate_mapping_review["source_inputs_required"]
    assert gmx_carry_inputs["display_unit_decision"]["manual_approval_id"] == "gmx_hourly_vs_annualized_display_decision"
    for carry_input in gmx_rate_mapping_review["carry_input_checklist"]:
        assert carry_input["manual_approval_required"] is True
        assert carry_input["manual_approval_id"]
        assert carry_input["blocked_by"]
        assert carry_input["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert carry_input["may_emit_carry_bps"] is False
        assert carry_input["may_estimate_cost_bps"] is False
        assert carry_input["may_rank_routes"] is False
        assert carry_input["may_submit_orders"] is False
        assert "no percent, bps" in carry_input["safe_use"]
        assert carry_input["next_action"]
    gmx_carry_evidence_summary = gmx_rate_mapping_review["carry_source_evidence_summary"]
    assert gmx_carry_evidence_summary["status"] == "evidence_required"
    assert gmx_carry_evidence_summary["evidence_count"] == 6
    assert gmx_carry_evidence_summary["blocked_evidence_count"] == 6
    assert gmx_carry_evidence_summary["evidence_ids"] == [
        "holding_period_runtime_input",
        "position_notional_runtime_input",
        "side_aware_sign_fixture_evidence",
        "source_helper_field_evidence",
        "display_unit_policy_evidence",
        "carry_manual_approval_evidence",
    ]
    assert gmx_carry_evidence_summary["evidence_type_ids"] == [
        "runtime_input",
        "fixture_case",
        "source_field",
        "policy_decision",
        "manual_approval",
    ]
    assert gmx_carry_evidence_summary["input_ids"] == [
        "holding_period_hours",
        "position_notional_usd",
        "rate_sign_convention",
        "source_helper_inputs",
        "display_unit_decision",
    ]
    assert sorted(gmx_carry_evidence_summary["required_source_inputs"]) == sorted(
        gmx_rate_mapping_review["source_inputs_required"]
    )
    assert gmx_carry_evidence_summary["required_fixture_case_ids"] == gmx_carry_summary["required_fixture_case_ids"]
    assert gmx_carry_evidence_summary["required_expectation_ids"] == expected_gmx_side_expectation_ids
    assert sorted(gmx_carry_evidence_summary["required_decision_check_ids"]) == sorted(
        [item["check_id"] for item in gmx_rate_mapping_review["mapping_decision_checklist"]]
    )
    assert gmx_carry_evidence_summary["required_manual_approval_ids"] == gmx_carry_summary["required_manual_approval_ids"]
    assert gmx_carry_evidence_summary["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
    assert gmx_carry_evidence_summary["may_emit_carry_bps"] is False
    assert gmx_carry_evidence_summary["may_estimate_cost_bps"] is False
    assert gmx_carry_evidence_summary["may_rank_routes"] is False
    assert gmx_carry_evidence_summary["may_submit_orders"] is False
    assert "no percent, bps" in gmx_carry_evidence_summary["safe_use"]
    assert gmx_carry_evidence_summary["next_action"]
    assert [item["evidence_id"] for item in gmx_rate_mapping_review["carry_source_evidence_checklist"]] == (
        gmx_carry_evidence_summary["evidence_ids"]
    )
    gmx_carry_evidence = {
        item["evidence_id"]: item
        for item in gmx_rate_mapping_review["carry_source_evidence_checklist"]
    }
    assert gmx_carry_evidence["holding_period_runtime_input"]["status"] == "input_required"
    assert gmx_carry_evidence["position_notional_runtime_input"]["status"] == "input_required"
    assert gmx_carry_evidence["side_aware_sign_fixture_evidence"]["status"] == "fixture_required"
    assert gmx_carry_evidence["source_helper_field_evidence"]["status"] == "source_inputs_missing"
    assert gmx_carry_evidence["display_unit_policy_evidence"]["status"] == "policy_input_required"
    assert gmx_carry_evidence["carry_manual_approval_evidence"]["status"] == "manual_approval_required"
    assert gmx_carry_evidence["side_aware_sign_fixture_evidence"]["evidence_type"] == "fixture_case"
    assert gmx_carry_evidence["source_helper_field_evidence"]["evidence_type"] == "source_field"
    assert gmx_carry_evidence["carry_manual_approval_evidence"]["evidence_type"] == "manual_approval"
    assert gmx_carry_evidence["source_helper_field_evidence"]["required_source_inputs"] == gmx_rate_mapping_review["source_inputs_required"]
    assert gmx_carry_evidence["carry_manual_approval_evidence"]["required_manual_approval_ids"] == gmx_carry_summary["required_manual_approval_ids"]
    for evidence in gmx_rate_mapping_review["carry_source_evidence_checklist"]:
        assert evidence["related_input_ids"]
        assert evidence["required_decision_check_ids"]
        assert evidence["required_manual_approval_ids"]
        assert evidence["blocked_by"]
        assert evidence["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert evidence["may_emit_carry_bps"] is False
        assert evidence["may_estimate_cost_bps"] is False
        assert evidence["may_rank_routes"] is False
        assert evidence["may_submit_orders"] is False
        assert "no percent, bps" in evidence["safe_use"]
        assert evidence["next_action"]
    gmx_live_helper_summary = gmx_rate_mapping_review["live_helper_source_summary"]
    expected_live_helper_review_ids = [
        "live_rate_output_fields_available",
        "nonzero_borrowing_relation_evidence",
        "helper_source_fields_presence",
        "side_direction_helper_fields",
        "manual_live_helper_mapping_review",
    ]
    assert gmx_live_helper_summary["status"] == "helper_source_review_required"
    assert gmx_live_helper_summary["review_count"] == 5
    assert gmx_live_helper_summary["blocked_review_count"] == 5
    assert gmx_live_helper_summary["review_ids"] == expected_live_helper_review_ids
    assert gmx_live_helper_summary["review_statuses"] == [
        "raw_outputs_available",
        "mapping_review_required",
        "source_inputs_missing",
        "fixture_required",
        "manual_approval_required",
    ]
    assert gmx_live_helper_summary["observed_source_fields"] == [
        "fundingRateLong",
        "fundingRateShort",
        "borrowingRateLong",
        "borrowingRateShort",
        "netRateLong",
        "netRateShort",
    ]
    assert gmx_live_helper_summary["required_source_inputs"] == gmx_rate_mapping_review["source_inputs_required"]
    assert gmx_live_helper_summary["present_source_inputs"] == []
    assert gmx_live_helper_summary["missing_source_inputs"] == gmx_rate_mapping_review["source_inputs_required"]
    assert gmx_live_helper_summary["fixture_case_ids"] == [
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "source_helper_inputs_presence",
        "longs_pay_shorts_direction",
    ]
    assert gmx_live_helper_summary["expectation_ids"] == expected_gmx_side_expectation_ids
    assert gmx_live_helper_summary["manual_approval_ids"] == [
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_source_helper_input_review",
        "gmx_side_aware_sign_review",
        "gmx_live_helper_source_review",
    ]
    assert gmx_live_helper_summary["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
    assert gmx_live_helper_summary["may_emit_carry_bps"] is False
    assert gmx_live_helper_summary["may_estimate_cost_bps"] is False
    assert gmx_live_helper_summary["may_rank_routes"] is False
    assert gmx_live_helper_summary["may_submit_orders"] is False
    assert "no percent, bps" in gmx_live_helper_summary["safe_use"]
    assert gmx_live_helper_summary["next_action"]
    assert [item["review_id"] for item in gmx_rate_mapping_review["live_helper_source_checklist"]] == (
        expected_live_helper_review_ids
    )
    gmx_live_helper_reviews = {
        item["review_id"]: item
        for item in gmx_rate_mapping_review["live_helper_source_checklist"]
    }
    assert gmx_live_helper_reviews["live_rate_output_fields_available"]["status"] == "raw_outputs_available"
    assert gmx_live_helper_reviews["nonzero_borrowing_relation_evidence"]["status"] == "mapping_review_required"
    assert gmx_live_helper_reviews["helper_source_fields_presence"]["status"] == "source_inputs_missing"
    assert gmx_live_helper_reviews["side_direction_helper_fields"]["status"] == "fixture_required"
    assert gmx_live_helper_reviews["manual_live_helper_mapping_review"]["status"] == "manual_approval_required"
    assert gmx_live_helper_reviews["live_rate_output_fields_available"]["observed_source_fields"] == (
        gmx_live_helper_summary["observed_source_fields"]
    )
    assert gmx_live_helper_reviews["helper_source_fields_presence"]["missing_source_inputs"] == (
        gmx_rate_mapping_review["source_inputs_required"]
    )
    assert gmx_live_helper_reviews["side_direction_helper_fields"]["expectation_ids"] == (
        expected_gmx_side_expectation_ids
    )
    assert gmx_live_helper_reviews["manual_live_helper_mapping_review"]["manual_approval_id"] == (
        "gmx_live_helper_source_review"
    )
    for helper_review in gmx_rate_mapping_review["live_helper_source_checklist"]:
        assert helper_review["review_label"]
        assert helper_review["source_scope"]
        assert isinstance(helper_review["evidence_count"], int)
        assert isinstance(helper_review["observed_source_fields"], list)
        assert isinstance(helper_review["required_source_inputs"], list)
        assert isinstance(helper_review["present_source_inputs"], list)
        assert isinstance(helper_review["missing_source_inputs"], list)
        assert helper_review["diagnostic_field_ids"]
        assert helper_review["fixture_case_ids"]
        assert helper_review["manual_approval_required"] is True
        assert helper_review["manual_approval_id"]
        assert helper_review["blocked_by"]
        assert helper_review["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert helper_review["may_emit_carry_bps"] is False
        assert helper_review["may_estimate_cost_bps"] is False
        assert helper_review["may_rank_routes"] is False
        assert helper_review["may_submit_orders"] is False
        assert "no percent, bps" in helper_review["safe_use"]
        assert helper_review["next_action"]
    gmx_helper_follow_up_summary = gmx_rate_mapping_review["helper_source_follow_up_summary"]
    expected_helper_follow_up_ids = [
        "source_helper_inputs_missing",
        "live_nonzero_mapping_approval",
        "side_direction_approval",
        "carry_runtime_policy_approvals",
    ]
    expected_helper_follow_up_statuses = [
        "source_inputs_missing",
        "mapping_review_required",
        "fixture_required",
        "manual_approval_required",
    ]
    assert gmx_helper_follow_up_summary["status"] == "follow_up_required"
    assert gmx_helper_follow_up_summary["follow_up_count"] == 4
    assert gmx_helper_follow_up_summary["blocked_follow_up_count"] == 4
    assert gmx_helper_follow_up_summary["follow_up_ids"] == expected_helper_follow_up_ids
    assert gmx_helper_follow_up_summary["follow_up_statuses"] == expected_helper_follow_up_statuses
    assert gmx_helper_follow_up_summary["related_input_ids"] == [
        "source_helper_inputs",
        "rate_sign_convention",
        "holding_period_hours",
        "position_notional_usd",
        "display_unit_decision",
    ]
    assert gmx_helper_follow_up_summary["related_review_ids"] == [
        "helper_source_fields_presence",
        "manual_live_helper_mapping_review",
        "live_rate_output_fields_available",
        "nonzero_borrowing_relation_evidence",
        "side_direction_helper_fields",
        "carry_conversion_boundary",
    ]
    assert gmx_helper_follow_up_summary["missing_source_inputs"] == gmx_rate_mapping_review["source_inputs_required"]
    assert gmx_helper_follow_up_summary["required_fixture_case_ids"] == [
        "source_helper_inputs_presence",
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
        "source_relation_raw_fields",
    ]
    assert gmx_helper_follow_up_summary["required_expectation_ids"] == expected_gmx_side_expectation_ids
    assert gmx_helper_follow_up_summary["required_decision_check_ids"] == [
        "source_helper_inputs_available",
        "nonzero_borrowing_relation_reviewed",
        "side_aware_direction_fixtures",
        "carry_inputs_defined",
        "display_unit_decision_recorded",
    ]
    assert gmx_helper_follow_up_summary["blocking_manual_approval_ids"] == [
        "gmx_source_helper_input_review",
        "gmx_live_helper_source_review",
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_side_aware_sign_review",
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    assert gmx_helper_follow_up_summary["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
    assert gmx_helper_follow_up_summary["may_emit_carry_bps"] is False
    assert gmx_helper_follow_up_summary["may_estimate_cost_bps"] is False
    assert gmx_helper_follow_up_summary["may_rank_routes"] is False
    assert gmx_helper_follow_up_summary["may_submit_orders"] is False
    assert "no percent, bps" in gmx_helper_follow_up_summary["safe_use"]
    assert gmx_helper_follow_up_summary["next_action"]
    assert [item["follow_up_id"] for item in gmx_rate_mapping_review["helper_source_follow_up_checklist"]] == (
        expected_helper_follow_up_ids
    )
    gmx_helper_follow_ups = {
        item["follow_up_id"]: item
        for item in gmx_rate_mapping_review["helper_source_follow_up_checklist"]
    }
    assert gmx_helper_follow_ups["source_helper_inputs_missing"]["missing_source_inputs"] == (
        gmx_rate_mapping_review["source_inputs_required"]
    )
    assert gmx_helper_follow_ups["live_nonzero_mapping_approval"]["blocking_manual_approval_ids"] == [
        "gmx_live_nonzero_borrowing_mapping_review"
    ]
    assert gmx_helper_follow_ups["side_direction_approval"]["required_expectation_ids"] == (
        expected_gmx_side_expectation_ids
    )
    assert gmx_helper_follow_ups["carry_runtime_policy_approvals"]["blocking_manual_approval_ids"] == [
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    for follow_up in gmx_rate_mapping_review["helper_source_follow_up_checklist"]:
        assert follow_up["follow_up_label"]
        assert follow_up["follow_up_type"]
        assert follow_up["related_input_ids"]
        assert follow_up["related_review_ids"]
        assert isinstance(follow_up["missing_source_inputs"], list)
        assert isinstance(follow_up["required_fixture_case_ids"], list)
        assert isinstance(follow_up["required_expectation_ids"], list)
        assert follow_up["required_decision_check_ids"]
        assert follow_up["blocking_manual_approval_ids"]
        assert follow_up["blocked_by"]
        assert follow_up["blocked_outputs"] == gmx_rate_mapping_review["blocked_outputs"]
        assert follow_up["may_emit_carry_bps"] is False
        assert follow_up["may_estimate_cost_bps"] is False
        assert follow_up["may_rank_routes"] is False
        assert follow_up["may_submit_orders"] is False
        assert "no percent, bps" in follow_up["safe_use"]
        assert follow_up["next_action"]

    blocker_ids = {blocker["id"] for blocker in model["blockers"]}
    assert "numeric_fee_inputs_missing" in blocker_ids
    assert "slippage_impact_inputs_missing" in blocker_ids
    assert "gmx_rate_semantics_pending" in blocker_ids
    assert "coinglass_enrichment_not_route_input" in blocker_ids
    assert "execution_boundary" in blocker_ids
    model_blockers = {blocker["id"]: blocker for blocker in model["blockers"]}
    assert "account_fee_tier" in model_blockers["numeric_fee_inputs_missing"]["missing_inputs"]
    assert "slippage_math" in model_blockers["slippage_impact_inputs_missing"]["missing_inputs"]
    assert "no_stale_depth_policy" in model_blockers["slippage_impact_inputs_missing"]["blocked_by"]
    assert "do not estimate executable slippage" in model_blockers["slippage_impact_inputs_missing"]["safe_use"]
    assert "holding_period_hours" in model_blockers["gmx_rate_semantics_pending"]["missing_inputs"]
    assert "direct_orderbook_depth" in model_blockers["coinglass_enrichment_not_route_input"]["missing_inputs"]
    assert "connector_write_path" in model_blockers["execution_boundary"]["missing_inputs"]


def test_perp_dex_coinglass_endpoint_is_read_only_research_enrichment() -> None:
    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")
    app.dependency_overrides[perp_dex.get_coinglass_client] = lambda: FakeCoinGlassPerpDexClient()

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/coinglass/markets?symbols=btc&exchanges=aster,lighter")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["read_only"] is True
    assert payload["meta"]["external_provider_calls"] is True
    assert payload["meta"]["source"] == "coinglass"
    assert payload["meta"]["requested_symbols"] == ["BTC"]
    assert payload["meta"]["requested_exchanges"] == ["Aster", "Lighter"]
    assert payload["meta"]["coverage_summary"]["direct_adapter_candidate_hints"] == ["Aster"]
    assert payload["meta"]["ranking_enabled"] is False
    assert payload["meta"]["production_signal_enabled"] is False

    snapshot = payload["data"]
    assert snapshot["read_only"] is True
    assert snapshot["execution_enabled"] is False
    assert snapshot["ranking_enabled"] is False
    assert snapshot["production_signal_enabled"] is False
    assert snapshot["normalization_status"] == "coinglass_coin_market_enrichment"
    assert snapshot["markets"][0]["venue_id"] == "coinglass:aster"
    assert snapshot["markets"][0]["provider_status"] == "third_party_aggregate"


def test_perp_dex_coinglass_endpoint_rejects_unknown_exchange() -> None:
    app = FastAPI()
    app.include_router(perp_dex.router, prefix="/api/v1")

    client = TestClient(app)
    response = client.get("/api/v1/perp-dex/venues/coinglass/markets?exchanges=UnknownDex")

    assert response.status_code == 400
    assert "unsupported CoinGlass Perp DEX exchange" in response.json()["detail"]
