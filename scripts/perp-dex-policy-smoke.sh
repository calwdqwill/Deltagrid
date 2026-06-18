#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
ALLOW_UNAVAILABLE="${ALLOW_UNAVAILABLE:-0}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMPARE_BASE_URL="${COMPARE_BASE_URL:-}"
FAIL_ON_DIFF="${FAIL_ON_DIFF:-0}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Perp DEX policy smoke.\n' >&2
    exit 1
  fi
fi

printf 'Perp DEX policy smoke ... '
"$PYTHON_BIN" - "$BASE_URL" "$ALLOW_UNAVAILABLE" "$TIMEOUT_SECONDS" "$COMPARE_BASE_URL" "$FAIL_ON_DIFF" <<'PY'
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

base_url, allow_raw, timeout_raw, compare_base_url, fail_on_diff_raw = sys.argv[1:6]
base_url = base_url.rstrip("/")
compare_base_url = compare_base_url.rstrip("/") if compare_base_url else ""
allow_unavailable = allow_raw == "1"
fail_on_diff = fail_on_diff_raw == "1"
timeout = int(timeout_raw)


def fetch_json(path, root_url=base_url):
    url = f"{root_url}{path}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "DeltaGridSmoke/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, {"success": False, "detail": str(exc)}
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        if allow_unavailable:
            return None, {"success": False, "detail": str(exc)}
        raise SystemExit(str(exc)) from exc


def require(condition, message, failures):
    if not condition:
        failures.append(message)


def require_structured_blockers(label, blockers, failures, require_scope=False):
    require(isinstance(blockers, list) and bool(blockers), f"{label}: blockers missing", failures)
    for index, blocker in enumerate(blockers if isinstance(blockers, list) else []):
        prefix = f"{label}[{index}]"
        require(isinstance(blocker.get("id"), str) and bool(blocker.get("id")), f"{prefix}: id missing", failures)
        require(
            isinstance(blocker.get("reason"), str) and bool(blocker.get("reason")),
            f"{prefix}: reason missing",
            failures,
        )
        require(
            isinstance(blocker.get("missing_inputs"), list) and bool(blocker.get("missing_inputs")),
            f"{prefix}: missing_inputs missing",
            failures,
        )
        require(
            isinstance(blocker.get("blocked_by"), list) and bool(blocker.get("blocked_by")),
            f"{prefix}: blocked_by missing",
            failures,
        )
        require(
            isinstance(blocker.get("safe_use"), str) and bool(blocker.get("safe_use")),
            f"{prefix}: safe_use missing",
            failures,
        )
        if require_scope:
            require(
                isinstance(blocker.get("scope"), str) and bool(blocker.get("scope")),
                f"{prefix}: scope missing",
                failures,
            )


def require_structured_required_inputs(required_inputs, failures):
    require(
        isinstance(required_inputs, list) and bool(required_inputs),
        "model.required_inputs: inputs missing",
        failures,
    )
    required_ids = {
        "venue_fee_schedule",
        "order_intent",
        "depth_or_impact_model",
        "carry_horizon",
        "risk_limits",
    }
    seen_ids = set()
    for index, item in enumerate(required_inputs if isinstance(required_inputs, list) else []):
        prefix = f"model.required_inputs[{index}]"
        item_id = item.get("id")
        seen_ids.add(item_id)
        require(isinstance(item_id, str) and bool(item_id), f"{prefix}: id missing", failures)
        require(
            isinstance(item.get("label"), str) and bool(item.get("label")),
            f"{prefix}: label missing",
            failures,
        )
        require(
            isinstance(item.get("reason"), str) and bool(item.get("reason")),
            f"{prefix}: reason missing",
            failures,
        )
    missing_ids = sorted(required_ids - seen_ids)
    require(not missing_ids, f"model.required_inputs: missing ids {missing_ids}", failures)


def require_formula_skeleton(formulas, failures):
    require(isinstance(formulas, dict) and bool(formulas), "model.formula_skeleton: missing", failures)
    required_keys = {"gross_edge_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"}
    formula_keys = set(formulas.keys()) if isinstance(formulas, dict) else set()
    missing_keys = sorted(required_keys - formula_keys)
    require(not missing_keys, f"model.formula_skeleton: missing keys {missing_keys}", failures)
    for key in sorted(required_keys & formula_keys):
        require(
            isinstance(formulas.get(key), str) and bool(formulas.get(key)),
            f"model.formula_skeleton.{key}: formula missing",
            failures,
        )


def compact_contract(policy, model):
    policy = policy if isinstance(policy, dict) else {}
    model = model if isinstance(model, dict) else {}
    policy_ui = policy.get("ui_policy") if isinstance(policy.get("ui_policy"), dict) else {}
    diagnostics = model.get("diagnostic_cost_estimate_v0")
    diagnostics = diagnostics if isinstance(diagnostics, dict) else {}
    summary = diagnostics.get("summary") if isinstance(diagnostics.get("summary"), dict) else {}
    components = diagnostics.get("components") if isinstance(diagnostics.get("components"), list) else []
    required_inputs = model.get("required_inputs") if isinstance(model.get("required_inputs"), list) else []
    source_breakdown = summary.get("source_field_breakdown") if isinstance(summary.get("source_field_breakdown"), list) else []
    safe_use_breakdown = summary.get("safe_use_breakdown") if isinstance(summary.get("safe_use_breakdown"), list) else []
    readiness_rollup = summary.get("readiness_rollup") if isinstance(summary.get("readiness_rollup"), list) else []
    fee_schedule_evidence_summary = (
        summary.get("fee_schedule_evidence_summary")
        if isinstance(summary.get("fee_schedule_evidence_summary"), dict)
        else {}
    )
    fee_schedule_evidence_checklist = (
        summary.get("fee_schedule_evidence_checklist")
        if isinstance(summary.get("fee_schedule_evidence_checklist"), list)
        else []
    )
    depth_checklist = (
        summary.get("depth_staleness_policy_checklist")
        if isinstance(summary.get("depth_staleness_policy_checklist"), list)
        else []
    )
    policy_input_breakdown = (
        summary.get("required_policy_input_breakdown")
        if isinstance(summary.get("required_policy_input_breakdown"), list)
        else []
    )
    next_action_breakdown = summary.get("next_action_breakdown") if isinstance(summary.get("next_action_breakdown"), list) else []
    source_input_action_coverage = (
        summary.get("source_input_action_coverage")
        if isinstance(summary.get("source_input_action_coverage"), list)
        else []
    )
    route_ready_evidence_checklist = (
        summary.get("route_ready_evidence_checklist")
        if isinstance(summary.get("route_ready_evidence_checklist"), list)
        else []
    )
    venue_evidence_status = (
        summary.get("venue_evidence_status")
        if isinstance(summary.get("venue_evidence_status"), list)
        else []
    )
    gmx_rate_mapping_review = model.get("gmx_rate_mapping_review_v0")
    gmx_rate_mapping_review = gmx_rate_mapping_review if isinstance(gmx_rate_mapping_review, dict) else {}
    gmx_review_items = (
        gmx_rate_mapping_review.get("review_items")
        if isinstance(gmx_rate_mapping_review.get("review_items"), list)
        else []
    )
    gmx_mapping_blocker_breakdown = (
        gmx_rate_mapping_review.get("blocker_breakdown")
        if isinstance(gmx_rate_mapping_review.get("blocker_breakdown"), list)
        else []
    )
    gmx_fixture_readiness_matrix = (
        gmx_rate_mapping_review.get("fixture_readiness_matrix")
        if isinstance(gmx_rate_mapping_review.get("fixture_readiness_matrix"), list)
        else []
    )
    gmx_side_aware_fixture_expectations = (
        gmx_rate_mapping_review.get("side_aware_fixture_expectations")
        if isinstance(gmx_rate_mapping_review.get("side_aware_fixture_expectations"), list)
        else []
    )
    gmx_mapping_decision_checklist = (
        gmx_rate_mapping_review.get("mapping_decision_checklist")
        if isinstance(gmx_rate_mapping_review.get("mapping_decision_checklist"), list)
        else []
    )
    gmx_carry_readiness_summary = (
        gmx_rate_mapping_review.get("carry_readiness_summary")
        if isinstance(gmx_rate_mapping_review.get("carry_readiness_summary"), dict)
        else {}
    )
    gmx_carry_input_checklist = (
        gmx_rate_mapping_review.get("carry_input_checklist")
        if isinstance(gmx_rate_mapping_review.get("carry_input_checklist"), list)
        else []
    )
    gmx_carry_evidence_summary = (
        gmx_rate_mapping_review.get("carry_source_evidence_summary")
        if isinstance(gmx_rate_mapping_review.get("carry_source_evidence_summary"), dict)
        else {}
    )
    gmx_carry_evidence_checklist = (
        gmx_rate_mapping_review.get("carry_source_evidence_checklist")
        if isinstance(gmx_rate_mapping_review.get("carry_source_evidence_checklist"), list)
        else []
    )
    gmx_live_helper_source_summary = (
        gmx_rate_mapping_review.get("live_helper_source_summary")
        if isinstance(gmx_rate_mapping_review.get("live_helper_source_summary"), dict)
        else {}
    )
    gmx_live_helper_source_checklist = (
        gmx_rate_mapping_review.get("live_helper_source_checklist")
        if isinstance(gmx_rate_mapping_review.get("live_helper_source_checklist"), list)
        else []
    )
    gmx_helper_source_follow_up_summary = (
        gmx_rate_mapping_review.get("helper_source_follow_up_summary")
        if isinstance(gmx_rate_mapping_review.get("helper_source_follow_up_summary"), dict)
        else {}
    )
    gmx_helper_source_follow_up_checklist = (
        gmx_rate_mapping_review.get("helper_source_follow_up_checklist")
        if isinstance(gmx_rate_mapping_review.get("helper_source_follow_up_checklist"), list)
        else []
    )
    return {
        "policy_status": policy.get("status"),
        "policy_read_only": policy.get("read_only"),
        "policy_execution_enabled": policy.get("execution_enabled"),
        "policy_may_rank_by_liquidity": policy_ui.get("may_rank_by_liquidity"),
        "model_status": model.get("status"),
        "model_read_only": model.get("read_only"),
        "model_execution_enabled": model.get("execution_enabled"),
        "model_ranking_enabled": model.get("ranking_enabled"),
        "may_emit_numeric_total_bps": diagnostics.get("may_emit_numeric_total_bps"),
        "component_ids": [item.get("id") for item in components if isinstance(item, dict)],
        "required_input_ids": [item.get("id") for item in required_inputs if isinstance(item, dict)],
        "source_fields": [item.get("source_field") for item in source_breakdown if isinstance(item, dict)],
        "safe_use_count": len(safe_use_breakdown),
        "readiness_rollup_ids": [item.get("category_id") for item in readiness_rollup if isinstance(item, dict)],
        "fee_schedule_evidence_status": fee_schedule_evidence_summary.get("status"),
        "fee_schedule_evidence_ids": [
            item.get("evidence_id")
            for item in fee_schedule_evidence_checklist
            if isinstance(item, dict)
        ],
        "fee_schedule_evidence_venue_ids": [
            item.get("venue_id")
            for item in fee_schedule_evidence_checklist
            if isinstance(item, dict)
        ],
        "fee_schedule_evidence_policy_inputs": fee_schedule_evidence_summary.get("required_policy_inputs", []),
        "fee_schedule_evidence_manual_approval_ids": fee_schedule_evidence_summary.get("manual_approval_ids", []),
        "depth_policy_ids": [item.get("policy_id") for item in depth_checklist if isinstance(item, dict)],
        "required_policy_input_ids": [item.get("input_id") for item in policy_input_breakdown if isinstance(item, dict)],
        "next_action_ids": [item.get("action_id") for item in next_action_breakdown if isinstance(item, dict)],
        "source_input_action_fields": [
            item.get("source_field")
            for item in source_input_action_coverage
            if isinstance(item, dict)
        ],
        "route_ready_evidence_gate_ids": [
            item.get("gate_id")
            for item in route_ready_evidence_checklist
            if isinstance(item, dict)
        ],
        "venue_evidence_status_ids": [
            item.get("venue_id")
            for item in venue_evidence_status
            if isinstance(item, dict)
        ],
        "gmx_rate_mapping_review_ids": [
            item.get("review_id")
            for item in gmx_review_items
            if isinstance(item, dict)
        ],
        "gmx_rate_mapping_status": {
            "status": gmx_rate_mapping_review.get("status"),
            "source_relation_status": gmx_rate_mapping_review.get("source_relation_status"),
            "live_mapping_status": gmx_rate_mapping_review.get("live_mapping_status"),
        },
        "gmx_rate_mapping_blocker_ids": [
            item.get("blocker_id")
            for item in gmx_mapping_blocker_breakdown
            if isinstance(item, dict)
        ],
        "gmx_rate_fixture_case_ids": [
            item.get("case_id")
            for item in gmx_fixture_readiness_matrix
            if isinstance(item, dict)
        ],
        "gmx_rate_fixture_statuses": {
            item.get("case_id"): item.get("status")
            for item in gmx_fixture_readiness_matrix
            if isinstance(item, dict) and item.get("case_id")
        },
        "gmx_rate_side_expectation_ids": [
            item.get("expectation_id")
            for item in gmx_side_aware_fixture_expectations
            if isinstance(item, dict)
        ],
        "gmx_rate_mapping_decision_check_ids": [
            item.get("check_id")
            for item in gmx_mapping_decision_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_mapping_decision_statuses": {
            item.get("check_id"): item.get("status")
            for item in gmx_mapping_decision_checklist
            if isinstance(item, dict) and item.get("check_id")
        },
        "gmx_rate_mapping_decision_manual_approval_ids": [
            item.get("manual_approval_id")
            for item in gmx_mapping_decision_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_carry_readiness_status": gmx_carry_readiness_summary.get("status"),
        "gmx_rate_carry_input_ids": [
            item.get("input_id")
            for item in gmx_carry_input_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_carry_input_statuses": {
            item.get("input_id"): item.get("status")
            for item in gmx_carry_input_checklist
            if isinstance(item, dict) and item.get("input_id")
        },
        "gmx_rate_carry_manual_approval_ids": gmx_carry_readiness_summary.get("required_manual_approval_ids", []),
        "gmx_rate_carry_evidence_status": gmx_carry_evidence_summary.get("status"),
        "gmx_rate_carry_evidence_ids": [
            item.get("evidence_id")
            for item in gmx_carry_evidence_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_carry_evidence_statuses": {
            item.get("evidence_id"): item.get("status")
            for item in gmx_carry_evidence_checklist
            if isinstance(item, dict) and item.get("evidence_id")
        },
        "gmx_rate_carry_evidence_types": {
            item.get("evidence_id"): item.get("evidence_type")
            for item in gmx_carry_evidence_checklist
            if isinstance(item, dict) and item.get("evidence_id")
        },
        "gmx_rate_carry_evidence_manual_approval_ids": gmx_carry_evidence_summary.get("required_manual_approval_ids", []),
        "gmx_rate_live_helper_review_status": gmx_live_helper_source_summary.get("status"),
        "gmx_rate_live_helper_review_ids": [
            item.get("review_id")
            for item in gmx_live_helper_source_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_live_helper_review_statuses": {
            item.get("review_id"): item.get("status")
            for item in gmx_live_helper_source_checklist
            if isinstance(item, dict) and item.get("review_id")
        },
        "gmx_rate_live_helper_missing_source_inputs": gmx_live_helper_source_summary.get("missing_source_inputs", []),
        "gmx_rate_live_helper_manual_approval_ids": gmx_live_helper_source_summary.get("manual_approval_ids", []),
        "gmx_rate_helper_follow_up_status": gmx_helper_source_follow_up_summary.get("status"),
        "gmx_rate_helper_follow_up_ids": [
            item.get("follow_up_id")
            for item in gmx_helper_source_follow_up_checklist
            if isinstance(item, dict)
        ],
        "gmx_rate_helper_follow_up_statuses": {
            item.get("follow_up_id"): item.get("status")
            for item in gmx_helper_source_follow_up_checklist
            if isinstance(item, dict) and item.get("follow_up_id")
        },
        "gmx_rate_helper_follow_up_missing_source_inputs": gmx_helper_source_follow_up_summary.get("missing_source_inputs", []),
        "gmx_rate_helper_follow_up_manual_approval_ids": gmx_helper_source_follow_up_summary.get("blocking_manual_approval_ids", []),
    }


def diff_contracts(base_contract, compare_contract):
    diffs = []
    field_names = sorted(set(base_contract) | set(compare_contract))
    for field in field_names:
        base_value = base_contract.get(field)
        compare_value = compare_contract.get(field)
        if base_value != compare_value:
            diffs.append({"field": field, "base": base_value, "compare": compare_value})
    return diffs


def require_diagnostic_components(diagnostics, required_inputs, failures):
    require(isinstance(diagnostics, dict) and bool(diagnostics), "model.diagnostic_cost_estimate_v0: missing", failures)
    require(
        diagnostics.get("status") == "blocked_for_numeric_total",
        "model.diagnostic_cost_estimate_v0: status must stay blocked_for_numeric_total",
        failures,
    )
    require(diagnostics.get("read_only") is True, "model.diagnostic_cost_estimate_v0: read_only must stay true", failures)
    require(
        diagnostics.get("may_emit_numeric_total_bps") is False,
        "model.diagnostic_cost_estimate_v0: numeric total bps must stay false",
        failures,
    )
    require(
        isinstance(diagnostics.get("safe_use"), str) and bool(diagnostics.get("safe_use")),
        "model.diagnostic_cost_estimate_v0: safe_use missing",
        failures,
    )
    require(
        isinstance(diagnostics.get("next_action"), str) and bool(diagnostics.get("next_action")),
        "model.diagnostic_cost_estimate_v0: next_action missing",
        failures,
    )

    components = diagnostics.get("components")
    require(
        isinstance(components, list) and bool(components),
        "model.diagnostic_cost_estimate_v0.components: missing",
        failures,
    )
    required_ids = {
        "lighter_fee_fields",
        "lighter_top_order_depth",
        "aster_published_fee_schedule",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
        "slippage_price_impact",
        "funding_borrow_carry",
    }
    component_items = components if isinstance(components, list) else []
    seen_ids = set()
    for index, component in enumerate(component_items):
        prefix = f"model.diagnostic_cost_estimate_v0.components[{index}]"
        component_id = component.get("id")
        seen_ids.add(component_id)
        require(isinstance(component_id, str) and bool(component_id), f"{prefix}: id missing", failures)
        require(isinstance(component.get("label"), str) and bool(component.get("label")), f"{prefix}: label missing", failures)
        require(
            isinstance(component.get("venue_id"), str) and bool(component.get("venue_id")),
            f"{prefix}: venue_id missing",
            failures,
        )
        require(isinstance(component.get("status"), str) and bool(component.get("status")), f"{prefix}: status missing", failures)
        require(isinstance(component.get("source_fields"), list), f"{prefix}: source_fields must be a list", failures)
        require(
            isinstance(component.get("may_emit_component_bps"), bool),
            f"{prefix}: may_emit_component_bps must be boolean",
            failures,
        )
        require(
            isinstance(component.get("required_input_ids"), list) and bool(component.get("required_input_ids")),
            f"{prefix}: required_input_ids missing",
            failures,
        )
        require(
            isinstance(component.get("blocked_by"), list) and bool(component.get("blocked_by")),
            f"{prefix}: blocked_by missing",
            failures,
        )
        require(isinstance(component.get("safe_use"), str) and bool(component.get("safe_use")), f"{prefix}: safe_use missing", failures)
        if component.get("may_emit_component_bps") is True:
            require(bool(component.get("source_fields")), f"{prefix}: display component needs source_fields", failures)
    missing_ids = sorted(required_ids - seen_ids)
    require(not missing_ids, f"model.diagnostic_cost_estimate_v0.components: missing ids {missing_ids}", failures)

    summary = diagnostics.get("summary")
    require(
        isinstance(summary, dict) and bool(summary),
        "model.diagnostic_cost_estimate_v0.summary: missing",
        failures,
    )
    summary = summary if isinstance(summary, dict) else {}
    expected_component_ids = [item.get("id") for item in component_items if isinstance(item, dict)]
    expected_display_ids = [
        item.get("id")
        for item in component_items
        if isinstance(item, dict) and item.get("may_emit_component_bps") is True
    ]
    expected_blocked_ids = [
        item.get("id")
        for item in component_items
        if isinstance(item, dict) and item.get("may_emit_component_bps") is not True
    ]
    expected_sourced_ids = [
        item.get("id")
        for item in component_items
        if isinstance(item, dict) and bool(item.get("source_fields"))
    ]
    require(summary.get("status") == diagnostics.get("status"), "model.diagnostic_cost_estimate_v0.summary: status mismatch", failures)
    require(
        summary.get("boundary") == "component_readiness_only",
        "model.diagnostic_cost_estimate_v0.summary: boundary mismatch",
        failures,
    )
    require(
        summary.get("component_count") == len(component_items),
        "model.diagnostic_cost_estimate_v0.summary: component_count mismatch",
        failures,
    )
    require(
        summary.get("display_only_component_count") == len(expected_display_ids),
        "model.diagnostic_cost_estimate_v0.summary: display count mismatch",
        failures,
    )
    require(
        summary.get("blocked_numeric_component_count") == len(expected_blocked_ids),
        "model.diagnostic_cost_estimate_v0.summary: blocked count mismatch",
        failures,
    )
    require(
        summary.get("sourced_component_count") == len(expected_sourced_ids),
        "model.diagnostic_cost_estimate_v0.summary: sourced count mismatch",
        failures,
    )
    require(
        summary.get("component_ids") == expected_component_ids,
        "model.diagnostic_cost_estimate_v0.summary: component_ids mismatch",
        failures,
    )
    require(
        summary.get("display_component_ids") == expected_display_ids,
        "model.diagnostic_cost_estimate_v0.summary: display_component_ids mismatch",
        failures,
    )
    require(
        summary.get("blocked_numeric_component_ids") == expected_blocked_ids,
        "model.diagnostic_cost_estimate_v0.summary: blocked ids mismatch",
        failures,
    )
    require(
        summary.get("sourced_component_ids") == expected_sourced_ids,
        "model.diagnostic_cost_estimate_v0.summary: sourced ids mismatch",
        failures,
    )
    require(
        summary.get("may_emit_numeric_total_bps") is False,
        "model.diagnostic_cost_estimate_v0.summary: numeric total must stay false",
        failures,
    )
    require(
        summary.get("numeric_total_status") == "blocked",
        "model.diagnostic_cost_estimate_v0.summary: numeric total status must stay blocked",
        failures,
    )
    require(
        summary.get("safe_use") == diagnostics.get("safe_use"),
        "model.diagnostic_cost_estimate_v0.summary: safe_use mismatch",
        failures,
    )
    require(
        summary.get("next_action") == diagnostics.get("next_action"),
        "model.diagnostic_cost_estimate_v0.summary: next_action mismatch",
        failures,
    )
    expected_venue_groups = {}
    for item in component_items:
        if not isinstance(item, dict):
            continue
        venue_id = item.get("venue_id") or "unknown"
        expected_venue_groups.setdefault(venue_id, []).append(item)
    venue_breakdown = summary.get("venue_breakdown")
    require(
        isinstance(venue_breakdown, list) and bool(venue_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.venue_breakdown: missing",
        failures,
    )
    breakdown_venue_ids = [
        item.get("venue_id")
        for item in venue_breakdown
        if isinstance(item, dict)
    ] if isinstance(venue_breakdown, list) else []
    require(
        breakdown_venue_ids == list(expected_venue_groups.keys()),
        "model.diagnostic_cost_estimate_v0.summary.venue_breakdown: venue order mismatch",
        failures,
    )
    for venue in venue_breakdown if isinstance(venue_breakdown, list) else []:
        if not isinstance(venue, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.venue_breakdown: venue row must be object")
            continue
        venue_prefix = f"model.diagnostic_cost_estimate_v0.summary.venue_breakdown.{venue.get('venue_id')}"
        venue_components = expected_venue_groups.get(venue.get("venue_id"), [])
        venue_display_ids = [
            item.get("id")
            for item in venue_components
            if item.get("may_emit_component_bps") is True
        ]
        venue_blocked_ids = [
            item.get("id")
            for item in venue_components
            if item.get("may_emit_component_bps") is not True
        ]
        venue_sourced_ids = [
            item.get("id")
            for item in venue_components
            if bool(item.get("source_fields"))
        ]
        require(isinstance(venue.get("venue_label"), str) and bool(venue.get("venue_label")), f"{venue_prefix}: label missing", failures)
        require(venue.get("component_count") == len(venue_components), f"{venue_prefix}: component_count mismatch", failures)
        require(
            venue.get("display_only_component_count") == len(venue_display_ids),
            f"{venue_prefix}: display count mismatch",
            failures,
        )
        require(
            venue.get("blocked_numeric_component_count") == len(venue_blocked_ids),
            f"{venue_prefix}: blocked count mismatch",
            failures,
        )
        require(
            venue.get("sourced_component_count") == len(venue_sourced_ids),
            f"{venue_prefix}: sourced count mismatch",
            failures,
        )
        require(
            venue.get("component_ids") == [item.get("id") for item in venue_components],
            f"{venue_prefix}: component_ids mismatch",
            failures,
        )
        require(venue.get("display_component_ids") == venue_display_ids, f"{venue_prefix}: display ids mismatch", failures)
        require(
            venue.get("blocked_numeric_component_ids") == venue_blocked_ids,
            f"{venue_prefix}: blocked ids mismatch",
            failures,
        )
        require(venue.get("sourced_component_ids") == venue_sourced_ids, f"{venue_prefix}: sourced ids mismatch", failures)
        require(venue.get("numeric_total_status") == "blocked", f"{venue_prefix}: numeric total status mismatch", failures)
        require(isinstance(venue.get("safe_use"), str) and bool(venue.get("safe_use")), f"{venue_prefix}: safe_use missing", failures)

    expected_blocker_groups = {}
    for item in component_items:
        if not isinstance(item, dict):
            continue
        for blocker in item.get("blocked_by", []):
            expected_blocker_groups.setdefault(str(blocker), []).append(item)
    blocker_breakdown = summary.get("blocker_breakdown")
    require(
        isinstance(blocker_breakdown, list) and bool(blocker_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.blocker_breakdown: missing",
        failures,
    )
    breakdown_blockers = [
        item.get("blocker")
        for item in blocker_breakdown
        if isinstance(item, dict)
    ] if isinstance(blocker_breakdown, list) else []
    require(
        breakdown_blockers == list(expected_blocker_groups.keys()),
        "model.diagnostic_cost_estimate_v0.summary.blocker_breakdown: blocker order mismatch",
        failures,
    )
    for blocker_row in blocker_breakdown if isinstance(blocker_breakdown, list) else []:
        if not isinstance(blocker_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.blocker_breakdown: blocker row must be object")
            continue
        blocker_prefix = f"model.diagnostic_cost_estimate_v0.summary.blocker_breakdown.{blocker_row.get('blocker')}"
        blocker_components = expected_blocker_groups.get(blocker_row.get("blocker"), [])
        blocker_venue_ids = []
        for item in blocker_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in blocker_venue_ids:
                blocker_venue_ids.append(venue_id)
        blocker_display_ids = [
            item.get("id")
            for item in blocker_components
            if item.get("may_emit_component_bps") is True
        ]
        blocker_blocked_ids = [
            item.get("id")
            for item in blocker_components
            if item.get("may_emit_component_bps") is not True
        ]
        require(
            isinstance(blocker_row.get("blocker"), str) and bool(blocker_row.get("blocker")),
            f"{blocker_prefix}: blocker missing",
            failures,
        )
        require(
            blocker_row.get("component_count") == len(blocker_components),
            f"{blocker_prefix}: component_count mismatch",
            failures,
        )
        require(
            blocker_row.get("component_ids") == [item.get("id") for item in blocker_components],
            f"{blocker_prefix}: component_ids mismatch",
            failures,
        )
        require(blocker_row.get("venue_ids") == blocker_venue_ids, f"{blocker_prefix}: venue_ids mismatch", failures)
        require(blocker_row.get("display_component_ids") == blocker_display_ids, f"{blocker_prefix}: display ids mismatch", failures)
        require(
            blocker_row.get("blocked_numeric_component_ids") == blocker_blocked_ids,
            f"{blocker_prefix}: blocked ids mismatch",
            failures,
        )
        require(blocker_row.get("numeric_total_status") == "blocked", f"{blocker_prefix}: numeric total status mismatch", failures)
        require(
            isinstance(blocker_row.get("safe_use"), str) and bool(blocker_row.get("safe_use")),
            f"{blocker_prefix}: safe_use missing",
            failures,
        )

    required_inputs = required_inputs if isinstance(required_inputs, list) else []
    expected_required_ids = [
        item.get("id")
        for item in required_inputs
        if isinstance(item, dict) and item.get("id")
    ]
    expected_required_groups = {}
    for item in component_items:
        if not isinstance(item, dict):
            continue
        for input_id in item.get("required_input_ids", []):
            expected_required_groups.setdefault(str(input_id), []).append(item)
    required_input_breakdown = summary.get("required_input_breakdown")
    require(
        isinstance(required_input_breakdown, list) and bool(required_input_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.required_input_breakdown: missing",
        failures,
    )
    breakdown_required_ids = [
        item.get("input_id")
        for item in required_input_breakdown
        if isinstance(item, dict)
    ] if isinstance(required_input_breakdown, list) else []
    require(
        breakdown_required_ids == expected_required_ids,
        "model.diagnostic_cost_estimate_v0.summary.required_input_breakdown: required input order mismatch",
        failures,
    )
    for input_row in required_input_breakdown if isinstance(required_input_breakdown, list) else []:
        if not isinstance(input_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.required_input_breakdown: row must be object")
            continue
        input_id = input_row.get("input_id")
        input_prefix = f"model.diagnostic_cost_estimate_v0.summary.required_input_breakdown.{input_id}"
        input_components = expected_required_groups.get(input_id, [])
        input_venue_ids = []
        for item in input_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in input_venue_ids:
                input_venue_ids.append(venue_id)
        input_display_ids = [
            item.get("id")
            for item in input_components
            if item.get("may_emit_component_bps") is True
        ]
        input_blocked_ids = [
            item.get("id")
            for item in input_components
            if item.get("may_emit_component_bps") is not True
        ]
        input_sourced_ids = [
            item.get("id")
            for item in input_components
            if bool(item.get("source_fields"))
        ]
        require(isinstance(input_row.get("input_id"), str) and bool(input_row.get("input_id")), f"{input_prefix}: input_id missing", failures)
        require(isinstance(input_row.get("input_label"), str) and bool(input_row.get("input_label")), f"{input_prefix}: label missing", failures)
        require(isinstance(input_row.get("status"), str) and bool(input_row.get("status")), f"{input_prefix}: status missing", failures)
        require(isinstance(input_row.get("reason"), str) and bool(input_row.get("reason")), f"{input_prefix}: reason missing", failures)
        require(input_row.get("component_count") == len(input_components), f"{input_prefix}: component_count mismatch", failures)
        require(input_row.get("component_ids") == [item.get("id") for item in input_components], f"{input_prefix}: component_ids mismatch", failures)
        require(input_row.get("venue_ids") == input_venue_ids, f"{input_prefix}: venue_ids mismatch", failures)
        require(input_row.get("display_component_ids") == input_display_ids, f"{input_prefix}: display ids mismatch", failures)
        require(input_row.get("blocked_numeric_component_ids") == input_blocked_ids, f"{input_prefix}: blocked ids mismatch", failures)
        require(input_row.get("sourced_component_ids") == input_sourced_ids, f"{input_prefix}: sourced ids mismatch", failures)
        require(input_row.get("numeric_total_status") == "blocked", f"{input_prefix}: numeric total status mismatch", failures)
        require(isinstance(input_row.get("safe_use"), str) and bool(input_row.get("safe_use")), f"{input_prefix}: safe_use missing", failures)
        require(isinstance(input_row.get("next_action"), str) and bool(input_row.get("next_action")), f"{input_prefix}: next_action missing", failures)
        if not input_components:
            require(input_row.get("status") == "route_gate_only", f"{input_prefix}: empty input should stay route_gate_only", failures)

    expected_source_groups = {}
    for item in component_items:
        if not isinstance(item, dict):
            continue
        for source_field in item.get("source_fields", []):
            expected_source_groups.setdefault(str(source_field), []).append(item)
    source_field_breakdown = summary.get("source_field_breakdown")
    require(
        isinstance(source_field_breakdown, list) and bool(source_field_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.source_field_breakdown: missing",
        failures,
    )
    breakdown_source_fields = [
        item.get("source_field")
        for item in source_field_breakdown
        if isinstance(item, dict)
    ] if isinstance(source_field_breakdown, list) else []
    require(
        breakdown_source_fields == list(expected_source_groups.keys()),
        "model.diagnostic_cost_estimate_v0.summary.source_field_breakdown: source field order mismatch",
        failures,
    )
    for source_row in source_field_breakdown if isinstance(source_field_breakdown, list) else []:
        if not isinstance(source_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.source_field_breakdown: row must be object")
            continue
        source_field = source_row.get("source_field")
        source_prefix = f"model.diagnostic_cost_estimate_v0.summary.source_field_breakdown.{source_field}"
        source_components = expected_source_groups.get(source_field, [])
        source_venue_ids = []
        source_required_ids = []
        for item in source_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in source_venue_ids:
                source_venue_ids.append(venue_id)
            for input_id in item.get("required_input_ids", []):
                if input_id not in source_required_ids:
                    source_required_ids.append(input_id)
        source_display_ids = [
            item.get("id")
            for item in source_components
            if item.get("may_emit_component_bps") is True
        ]
        source_blocked_ids = [
            item.get("id")
            for item in source_components
            if item.get("may_emit_component_bps") is not True
        ]
        require(source_row.get("status") == "display_context_only", f"{source_prefix}: status mismatch", failures)
        require(source_row.get("component_count") == len(source_components), f"{source_prefix}: component_count mismatch", failures)
        require(source_row.get("component_ids") == [item.get("id") for item in source_components], f"{source_prefix}: component_ids mismatch", failures)
        require(source_row.get("venue_ids") == source_venue_ids, f"{source_prefix}: venue_ids mismatch", failures)
        require(source_row.get("required_input_ids") == source_required_ids, f"{source_prefix}: required_input_ids mismatch", failures)
        require(source_row.get("display_component_ids") == source_display_ids, f"{source_prefix}: display ids mismatch", failures)
        require(source_row.get("blocked_numeric_component_ids") == source_blocked_ids, f"{source_prefix}: blocked ids mismatch", failures)
        require(source_row.get("numeric_total_status") == "blocked", f"{source_prefix}: numeric total status mismatch", failures)
        require(isinstance(source_row.get("safe_use"), str) and bool(source_row.get("safe_use")), f"{source_prefix}: safe_use missing", failures)

    expected_safe_use_groups = {}
    for item in component_items:
        if not isinstance(item, dict):
            continue
        safe_use = item.get("safe_use")
        if safe_use:
            expected_safe_use_groups.setdefault(str(safe_use), []).append(item)
    safe_use_breakdown = summary.get("safe_use_breakdown")
    require(
        isinstance(safe_use_breakdown, list) and bool(safe_use_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.safe_use_breakdown: missing",
        failures,
    )
    breakdown_safe_uses = [
        item.get("safe_use")
        for item in safe_use_breakdown
        if isinstance(item, dict)
    ] if isinstance(safe_use_breakdown, list) else []
    require(
        breakdown_safe_uses == list(expected_safe_use_groups.keys()),
        "model.diagnostic_cost_estimate_v0.summary.safe_use_breakdown: safe_use order mismatch",
        failures,
    )
    for safe_use_row in safe_use_breakdown if isinstance(safe_use_breakdown, list) else []:
        if not isinstance(safe_use_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.safe_use_breakdown: row must be object")
            continue
        safe_use = safe_use_row.get("safe_use")
        safe_prefix = f"model.diagnostic_cost_estimate_v0.summary.safe_use_breakdown.{safe_use}"
        safe_components = expected_safe_use_groups.get(safe_use, [])
        safe_venue_ids = []
        safe_required_ids = []
        for item in safe_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in safe_venue_ids:
                safe_venue_ids.append(venue_id)
            for input_id in item.get("required_input_ids", []):
                if input_id not in safe_required_ids:
                    safe_required_ids.append(input_id)
        safe_display_ids = [
            item.get("id")
            for item in safe_components
            if item.get("may_emit_component_bps") is True
        ]
        safe_blocked_ids = [
            item.get("id")
            for item in safe_components
            if item.get("may_emit_component_bps") is not True
        ]
        require(safe_use_row.get("status") == "boundary_notice", f"{safe_prefix}: status mismatch", failures)
        require(safe_use_row.get("component_count") == len(safe_components), f"{safe_prefix}: component_count mismatch", failures)
        require(safe_use_row.get("component_ids") == [item.get("id") for item in safe_components], f"{safe_prefix}: component_ids mismatch", failures)
        require(safe_use_row.get("venue_ids") == safe_venue_ids, f"{safe_prefix}: venue_ids mismatch", failures)
        require(safe_use_row.get("required_input_ids") == safe_required_ids, f"{safe_prefix}: required_input_ids mismatch", failures)
        require(safe_use_row.get("display_component_ids") == safe_display_ids, f"{safe_prefix}: display ids mismatch", failures)
        require(safe_use_row.get("blocked_numeric_component_ids") == safe_blocked_ids, f"{safe_prefix}: blocked ids mismatch", failures)
        require(safe_use_row.get("numeric_total_status") == "blocked", f"{safe_prefix}: numeric total status mismatch", failures)
        require(isinstance(safe_use_row.get("next_action"), str) and bool(safe_use_row.get("next_action")), f"{safe_prefix}: next_action missing", failures)

    readiness_rollup = summary.get("readiness_rollup")
    require(
        isinstance(readiness_rollup, list) and bool(readiness_rollup),
        "model.diagnostic_cost_estimate_v0.summary.readiness_rollup: missing",
        failures,
    )
    expected_rollup_ids = ["fees", "depth_slippage", "carry", "risk_limits"]
    rollup_ids = [
        item.get("category_id")
        for item in readiness_rollup
        if isinstance(item, dict)
    ] if isinstance(readiness_rollup, list) else []
    require(rollup_ids == expected_rollup_ids, "model.diagnostic_cost_estimate_v0.summary.readiness_rollup: category order mismatch", failures)
    for rollup in readiness_rollup if isinstance(readiness_rollup, list) else []:
        if not isinstance(rollup, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.readiness_rollup: row must be object")
            continue
        rollup_prefix = f"model.diagnostic_cost_estimate_v0.summary.readiness_rollup.{rollup.get('category_id')}"
        require(isinstance(rollup.get("category_label"), str) and bool(rollup.get("category_label")), f"{rollup_prefix}: label missing", failures)
        require(isinstance(rollup.get("status"), str) and bool(rollup.get("status")), f"{rollup_prefix}: status missing", failures)
        require(isinstance(rollup.get("required_input_ids"), list) and bool(rollup.get("required_input_ids")), f"{rollup_prefix}: required_input_ids missing", failures)
        require(isinstance(rollup.get("component_count"), int), f"{rollup_prefix}: component_count missing", failures)
        require(isinstance(rollup.get("sourced_component_count"), int), f"{rollup_prefix}: sourced_component_count missing", failures)
        require(isinstance(rollup.get("display_component_ids"), list), f"{rollup_prefix}: display_component_ids missing", failures)
        require(isinstance(rollup.get("blocked_numeric_component_ids"), list), f"{rollup_prefix}: blocked_numeric_component_ids missing", failures)
        require(rollup.get("numeric_total_status") == "blocked", f"{rollup_prefix}: numeric total status mismatch", failures)
        require(isinstance(rollup.get("safe_use"), str) and bool(rollup.get("safe_use")), f"{rollup_prefix}: safe_use missing", failures)
        require(isinstance(rollup.get("next_action"), str) and bool(rollup.get("next_action")), f"{rollup_prefix}: next_action missing", failures)

    fee_schedule_evidence_summary = summary.get("fee_schedule_evidence_summary")
    require(
        isinstance(fee_schedule_evidence_summary, dict) and bool(fee_schedule_evidence_summary),
        "model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_summary: missing",
        failures,
    )
    fee_schedule_evidence_checklist = summary.get("fee_schedule_evidence_checklist")
    require(
        isinstance(fee_schedule_evidence_checklist, list) and bool(fee_schedule_evidence_checklist),
        "model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_checklist: missing",
        failures,
    )
    expected_fee_evidence_ids = ["lighter_fee_schedule_evidence", "aster_fee_schedule_evidence"]
    expected_fee_venue_ids = ["lighter", "aster"]
    expected_fee_component_ids = ["lighter_fee_fields", "aster_published_fee_schedule"]
    expected_fee_required_inputs = ["venue_fee_schedule", "order_intent"]
    expected_fee_policy_inputs = [
        "account_fee_tier",
        "fee_unit_confirmation",
        "maker_taker_side",
        "order_side",
        "order_size_usd",
        "order_intent_type",
        "reduce_only_or_opening_intent",
        "fee_schedule_source_confirmation",
        "fee_discount_policy",
    ]
    expected_fee_manual_approval_ids = [
        "lighter_fee_unit_review",
        "lighter_account_fee_tier_review",
        "lighter_order_intent_fee_review",
        "aster_fee_schedule_source_review",
        "aster_account_fee_tier_review",
        "aster_fee_discount_policy_review",
        "aster_order_intent_fee_review",
    ]
    expected_fee_blocked_outputs = ["fee_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"]
    if isinstance(fee_schedule_evidence_summary, dict):
        summary_prefix = "model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_summary"
        require(fee_schedule_evidence_summary.get("status") == "fee_schedule_evidence_required", f"{summary_prefix}: status mismatch", failures)
        require(fee_schedule_evidence_summary.get("evidence_count") == 2, f"{summary_prefix}: evidence_count mismatch", failures)
        require(fee_schedule_evidence_summary.get("blocked_evidence_count") == 2, f"{summary_prefix}: blocked count mismatch", failures)
        require(fee_schedule_evidence_summary.get("venue_ids") == expected_fee_venue_ids, f"{summary_prefix}: venue ids mismatch", failures)
        require(fee_schedule_evidence_summary.get("component_ids") == expected_fee_component_ids, f"{summary_prefix}: component ids mismatch", failures)
        require(fee_schedule_evidence_summary.get("required_input_ids") == expected_fee_required_inputs, f"{summary_prefix}: required inputs mismatch", failures)
        require(fee_schedule_evidence_summary.get("required_policy_inputs") == expected_fee_policy_inputs, f"{summary_prefix}: policy inputs mismatch", failures)
        require(fee_schedule_evidence_summary.get("manual_approval_ids") == expected_fee_manual_approval_ids, f"{summary_prefix}: manual approvals mismatch", failures)
        require(fee_schedule_evidence_summary.get("blocked_outputs") == expected_fee_blocked_outputs, f"{summary_prefix}: blocked outputs mismatch", failures)
        require(fee_schedule_evidence_summary.get("may_emit_fee_bps") is False, f"{summary_prefix}: fee bps must stay blocked", failures)
        require(fee_schedule_evidence_summary.get("may_estimate_cost_bps") is False, f"{summary_prefix}: cost bps must stay blocked", failures)
        require(fee_schedule_evidence_summary.get("may_rank_routes") is False, f"{summary_prefix}: ranking must stay blocked", failures)
        require(fee_schedule_evidence_summary.get("may_submit_orders") is False, f"{summary_prefix}: execution must stay blocked", failures)
        require(fee_schedule_evidence_summary.get("numeric_total_status") == "blocked", f"{summary_prefix}: numeric total status mismatch", failures)
        require(
            isinstance(fee_schedule_evidence_summary.get("safe_use"), str)
            and "do not emit fee bps" in fee_schedule_evidence_summary.get("safe_use"),
            f"{summary_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(fee_schedule_evidence_summary.get("next_action"), str) and bool(fee_schedule_evidence_summary.get("next_action")), f"{summary_prefix}: next_action missing", failures)
    fee_evidence_ids = [
        item.get("evidence_id")
        for item in fee_schedule_evidence_checklist
        if isinstance(item, dict)
    ] if isinstance(fee_schedule_evidence_checklist, list) else []
    require(
        fee_evidence_ids == expected_fee_evidence_ids,
        "model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_checklist: evidence order mismatch",
        failures,
    )
    for evidence in fee_schedule_evidence_checklist if isinstance(fee_schedule_evidence_checklist, list) else []:
        if not isinstance(evidence, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_checklist: row must be object")
            continue
        evidence_prefix = f"model.diagnostic_cost_estimate_v0.summary.fee_schedule_evidence_checklist.{evidence.get('evidence_id')}"
        require(evidence.get("venue_id") in expected_fee_venue_ids, f"{evidence_prefix}: venue mismatch", failures)
        require(evidence.get("status") == "fee_policy_required", f"{evidence_prefix}: status mismatch", failures)
        require(evidence.get("source_component_id") in expected_fee_component_ids, f"{evidence_prefix}: component mismatch", failures)
        require(isinstance(evidence.get("source_fields"), list) and bool(evidence.get("source_fields")), f"{evidence_prefix}: source fields missing", failures)
        require(evidence.get("required_input_ids") == expected_fee_required_inputs, f"{evidence_prefix}: required inputs mismatch", failures)
        require(isinstance(evidence.get("required_policy_inputs"), list) and bool(evidence.get("required_policy_inputs")), f"{evidence_prefix}: policy inputs missing", failures)
        require(isinstance(evidence.get("manual_approval_ids"), list) and bool(evidence.get("manual_approval_ids")), f"{evidence_prefix}: manual approvals missing", failures)
        require(isinstance(evidence.get("blocked_by"), list) and bool(evidence.get("blocked_by")), f"{evidence_prefix}: blockers missing", failures)
        require(evidence.get("blocked_outputs") == expected_fee_blocked_outputs, f"{evidence_prefix}: blocked outputs mismatch", failures)
        require(evidence.get("may_emit_fee_bps") is False, f"{evidence_prefix}: fee bps must stay blocked", failures)
        require(evidence.get("may_estimate_cost_bps") is False, f"{evidence_prefix}: cost bps must stay blocked", failures)
        require(evidence.get("may_rank_routes") is False, f"{evidence_prefix}: ranking must stay blocked", failures)
        require(evidence.get("may_submit_orders") is False, f"{evidence_prefix}: execution must stay blocked", failures)
        require(evidence.get("numeric_total_status") == "blocked", f"{evidence_prefix}: numeric total status mismatch", failures)
        require(isinstance(evidence.get("safe_use"), str) and bool(evidence.get("safe_use")), f"{evidence_prefix}: safe_use missing", failures)
        require(isinstance(evidence.get("next_action"), str) and bool(evidence.get("next_action")), f"{evidence_prefix}: next_action missing", failures)

    depth_checklist = summary.get("depth_staleness_policy_checklist")
    require(
        isinstance(depth_checklist, list) and bool(depth_checklist),
        "model.diagnostic_cost_estimate_v0.summary.depth_staleness_policy_checklist: missing",
        failures,
    )
    expected_depth_policy_ids = [
        "lighter_top_order_depth_staleness",
        "aster_top_of_book_staleness",
        "aster_depth_ladder_staleness",
    ]
    expected_depth_component_ids = [
        "lighter_top_order_depth",
        "aster_top_of_book_spread",
        "aster_depth_ladder",
    ]
    depth_policy_ids = [
        item.get("policy_id")
        for item in depth_checklist
        if isinstance(item, dict)
    ] if isinstance(depth_checklist, list) else []
    depth_component_ids = [
        item.get("component_id")
        for item in depth_checklist
        if isinstance(item, dict)
    ] if isinstance(depth_checklist, list) else []
    require(
        depth_policy_ids == expected_depth_policy_ids,
        "model.diagnostic_cost_estimate_v0.summary.depth_staleness_policy_checklist: policy order mismatch",
        failures,
    )
    require(
        depth_component_ids == expected_depth_component_ids,
        "model.diagnostic_cost_estimate_v0.summary.depth_staleness_policy_checklist: component order mismatch",
        failures,
    )
    components_by_id = {
        item.get("id"): item
        for item in component_items
        if isinstance(item, dict)
    }
    required_depth_policy_inputs = [
        "depth_snapshot_timestamp",
        "max_depth_age_ms",
        "stale_depth_action",
        "order_size_usd",
        "side",
        "depth_aggregation_policy",
        "liquidity_cap",
    ]
    for policy in depth_checklist if isinstance(depth_checklist, list) else []:
        if not isinstance(policy, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.depth_staleness_policy_checklist: row must be object")
            continue
        policy_prefix = f"model.diagnostic_cost_estimate_v0.summary.depth_staleness_policy_checklist.{policy.get('policy_id')}"
        component = components_by_id.get(policy.get("component_id"), {})
        require(isinstance(policy.get("venue_id"), str) and bool(policy.get("venue_id")), f"{policy_prefix}: venue_id missing", failures)
        require(isinstance(policy.get("venue_label"), str) and bool(policy.get("venue_label")), f"{policy_prefix}: venue_label missing", failures)
        require(isinstance(policy.get("depth_scope"), str) and bool(policy.get("depth_scope")), f"{policy_prefix}: depth_scope missing", failures)
        require(isinstance(policy.get("source_endpoint"), str) and bool(policy.get("source_endpoint")), f"{policy_prefix}: source_endpoint missing", failures)
        require(policy.get("status") == "staleness_policy_required", f"{policy_prefix}: status mismatch", failures)
        require(policy.get("source_fields") == component.get("source_fields"), f"{policy_prefix}: source_fields mismatch", failures)
        require(policy.get("required_policy_inputs") == required_depth_policy_inputs, f"{policy_prefix}: required policy inputs mismatch", failures)
        require(
            policy.get("blocked_by") == [
                "no_depth_snapshot_timestamp",
                "no_max_depth_age_ms",
                "no_stale_depth_action",
                "no_order_size_context",
            ],
            f"{policy_prefix}: blockers mismatch",
            failures,
        )
        require(policy.get("may_emit_slippage_bps") is False, f"{policy_prefix}: slippage bps must stay blocked", failures)
        require(policy.get("numeric_total_status") == "blocked", f"{policy_prefix}: numeric total status mismatch", failures)
        require(isinstance(policy.get("safe_use"), str) and "do not estimate slippage" in policy.get("safe_use"), f"{policy_prefix}: safe_use mismatch", failures)
        require(isinstance(policy.get("next_action"), str) and bool(policy.get("next_action")), f"{policy_prefix}: next_action missing", failures)

    required_policy_input_breakdown = summary.get("required_policy_input_breakdown")
    require(
        isinstance(required_policy_input_breakdown, list) and bool(required_policy_input_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.required_policy_input_breakdown: missing",
        failures,
    )
    policy_input_ids = [
        item.get("input_id")
        for item in required_policy_input_breakdown
        if isinstance(item, dict)
    ] if isinstance(required_policy_input_breakdown, list) else []
    require(
        policy_input_ids == required_depth_policy_inputs,
        "model.diagnostic_cost_estimate_v0.summary.required_policy_input_breakdown: input order mismatch",
        failures,
    )
    expected_policy_ids = [
        item.get("policy_id")
        for item in depth_checklist
        if isinstance(item, dict)
    ] if isinstance(depth_checklist, list) else []
    expected_policy_component_ids = []
    expected_policy_venue_ids = []
    expected_policy_source_endpoints = []
    expected_policy_blockers = []
    for policy in depth_checklist if isinstance(depth_checklist, list) else []:
        if not isinstance(policy, dict):
            continue
        for value, target in (
            (policy.get("component_id"), expected_policy_component_ids),
            (policy.get("venue_id"), expected_policy_venue_ids),
            (policy.get("source_endpoint"), expected_policy_source_endpoints),
        ):
            if value and value not in target:
                target.append(value)
        for blocker in policy.get("blocked_by", []):
            if blocker and blocker not in expected_policy_blockers:
                expected_policy_blockers.append(blocker)
    for input_row in required_policy_input_breakdown if isinstance(required_policy_input_breakdown, list) else []:
        if not isinstance(input_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.required_policy_input_breakdown: row must be object")
            continue
        input_prefix = f"model.diagnostic_cost_estimate_v0.summary.required_policy_input_breakdown.{input_row.get('input_id')}"
        require(isinstance(input_row.get("input_label"), str) and bool(input_row.get("input_label")), f"{input_prefix}: label missing", failures)
        require(input_row.get("status") == "policy_input_required", f"{input_prefix}: status mismatch", failures)
        require(input_row.get("policy_count") == len(expected_policy_ids), f"{input_prefix}: policy_count mismatch", failures)
        require(input_row.get("policy_ids") == expected_policy_ids, f"{input_prefix}: policy_ids mismatch", failures)
        require(input_row.get("component_ids") == expected_policy_component_ids, f"{input_prefix}: component_ids mismatch", failures)
        require(input_row.get("venue_ids") == expected_policy_venue_ids, f"{input_prefix}: venue_ids mismatch", failures)
        require(input_row.get("source_endpoints") == expected_policy_source_endpoints, f"{input_prefix}: source_endpoints mismatch", failures)
        require(input_row.get("blocked_by") == expected_policy_blockers, f"{input_prefix}: blockers mismatch", failures)
        require(input_row.get("may_emit_slippage_bps") is False, f"{input_prefix}: slippage bps must stay blocked", failures)
        require(input_row.get("numeric_total_status") == "blocked", f"{input_prefix}: numeric total status mismatch", failures)
        require(
            isinstance(input_row.get("safe_use"), str) and "do not estimate slippage" in input_row.get("safe_use"),
            f"{input_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(input_row.get("next_action"), str) and bool(input_row.get("next_action")), f"{input_prefix}: next_action missing", failures)

    next_action_breakdown = summary.get("next_action_breakdown")
    require(
        isinstance(next_action_breakdown, list) and bool(next_action_breakdown),
        "model.diagnostic_cost_estimate_v0.summary.next_action_breakdown: missing",
        failures,
    )
    expected_next_actions = []
    for row in required_input_breakdown if isinstance(required_input_breakdown, list) else []:
        if isinstance(row, dict) and row.get("next_action") not in expected_next_actions:
            expected_next_actions.append(row.get("next_action"))
    for row in readiness_rollup if isinstance(readiness_rollup, list) else []:
        if isinstance(row, dict) and row.get("next_action") not in expected_next_actions:
            expected_next_actions.append(row.get("next_action"))
    for row in depth_checklist if isinstance(depth_checklist, list) else []:
        if isinstance(row, dict) and row.get("next_action") not in expected_next_actions:
            expected_next_actions.append(row.get("next_action"))
    breakdown_next_actions = [
        item.get("next_action")
        for item in next_action_breakdown
        if isinstance(item, dict)
    ] if isinstance(next_action_breakdown, list) else []
    require(
        breakdown_next_actions == expected_next_actions,
        "model.diagnostic_cost_estimate_v0.summary.next_action_breakdown: next_action order mismatch",
        failures,
    )
    for index, action in enumerate(next_action_breakdown if isinstance(next_action_breakdown, list) else [], start=1):
        if not isinstance(action, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.next_action_breakdown: row must be object")
            continue
        action_prefix = f"model.diagnostic_cost_estimate_v0.summary.next_action_breakdown.{action.get('action_id')}"
        require(action.get("action_id") == f"next_action_{index}", f"{action_prefix}: action_id mismatch", failures)
        require(isinstance(action.get("next_action"), str) and bool(action.get("next_action")), f"{action_prefix}: next_action missing", failures)
        require(action.get("status") == "action_required", f"{action_prefix}: status mismatch", failures)
        require(isinstance(action.get("source_count"), int) and action.get("source_count") > 0, f"{action_prefix}: source_count mismatch", failures)
        require(isinstance(action.get("source_types"), list) and bool(action.get("source_types")), f"{action_prefix}: source_types missing", failures)
        require(isinstance(action.get("source_ids"), list) and bool(action.get("source_ids")), f"{action_prefix}: source_ids missing", failures)
        require(isinstance(action.get("required_input_ids"), list), f"{action_prefix}: required_input_ids missing", failures)
        require(isinstance(action.get("required_policy_inputs"), list), f"{action_prefix}: required_policy_inputs missing", failures)
        require(isinstance(action.get("component_ids"), list), f"{action_prefix}: component_ids missing", failures)
        require(isinstance(action.get("venue_ids"), list), f"{action_prefix}: venue_ids missing", failures)
        require(isinstance(action.get("policy_ids"), list), f"{action_prefix}: policy_ids missing", failures)
        require(isinstance(action.get("rollup_category_ids"), list), f"{action_prefix}: rollup_category_ids missing", failures)
        require(action.get("numeric_total_status") == "blocked", f"{action_prefix}: numeric total status mismatch", failures)
        require(
            isinstance(action.get("safe_use"), str) and "do not estimate route cost" in action.get("safe_use"),
            f"{action_prefix}: safe_use mismatch",
            failures,
        )

    source_input_action_coverage = summary.get("source_input_action_coverage")
    require(
        isinstance(source_input_action_coverage, list) and bool(source_input_action_coverage),
        "model.diagnostic_cost_estimate_v0.summary.source_input_action_coverage: missing",
        failures,
    )
    coverage_source_fields = [
        item.get("source_field")
        for item in source_input_action_coverage
        if isinstance(item, dict)
    ] if isinstance(source_input_action_coverage, list) else []
    require(
        coverage_source_fields == list(expected_source_groups.keys()),
        "model.diagnostic_cost_estimate_v0.summary.source_input_action_coverage: source field order mismatch",
        failures,
    )
    for index, coverage_row in enumerate(source_input_action_coverage if isinstance(source_input_action_coverage, list) else [], start=1):
        if not isinstance(coverage_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.source_input_action_coverage: row must be object")
            continue
        source_field = coverage_row.get("source_field")
        coverage_prefix = f"model.diagnostic_cost_estimate_v0.summary.source_input_action_coverage.{source_field}"
        source_components = expected_source_groups.get(source_field, [])
        source_component_ids = [item.get("id") for item in source_components]
        source_venue_ids = []
        source_required_ids = []
        for item in source_components:
            venue_id = item.get("venue_id") or "unknown"
            if venue_id not in source_venue_ids:
                source_venue_ids.append(venue_id)
            for input_id in item.get("required_input_ids", []):
                if input_id not in source_required_ids:
                    source_required_ids.append(input_id)
        matched_actions = []
        for action in next_action_breakdown if isinstance(next_action_breakdown, list) else []:
            if not isinstance(action, dict):
                continue
            action_required_ids = action.get("required_input_ids") if isinstance(action.get("required_input_ids"), list) else []
            action_component_ids = action.get("component_ids") if isinstance(action.get("component_ids"), list) else []
            if any(input_id in action_required_ids for input_id in source_required_ids) or any(
                component_id in action_component_ids for component_id in source_component_ids
            ):
                matched_actions.append(action)
        matched_source_types = []
        for action in matched_actions:
            for source_type in action.get("source_types", []):
                if source_type not in matched_source_types:
                    matched_source_types.append(source_type)
        source_display_ids = [
            item.get("id")
            for item in source_components
            if item.get("may_emit_component_bps") is True
        ]
        source_blocked_ids = [
            item.get("id")
            for item in source_components
            if item.get("may_emit_component_bps") is not True
        ]
        require(coverage_row.get("coverage_id") == f"source_field_{index}", f"{coverage_prefix}: coverage_id mismatch", failures)
        require(coverage_row.get("status") == "display_context_only", f"{coverage_prefix}: status mismatch", failures)
        require(coverage_row.get("component_count") == len(source_components), f"{coverage_prefix}: component_count mismatch", failures)
        require(coverage_row.get("component_ids") == source_component_ids, f"{coverage_prefix}: component_ids mismatch", failures)
        require(coverage_row.get("venue_ids") == source_venue_ids, f"{coverage_prefix}: venue_ids mismatch", failures)
        require(coverage_row.get("required_input_count") == len(source_required_ids), f"{coverage_prefix}: required_input_count mismatch", failures)
        require(coverage_row.get("required_input_ids") == source_required_ids, f"{coverage_prefix}: required_input_ids mismatch", failures)
        require(coverage_row.get("next_action_count") == len(matched_actions), f"{coverage_prefix}: next_action_count mismatch", failures)
        require(coverage_row.get("next_action_ids") == [action.get("action_id") for action in matched_actions], f"{coverage_prefix}: next_action_ids mismatch", failures)
        require(coverage_row.get("next_actions") == [action.get("next_action") for action in matched_actions], f"{coverage_prefix}: next_actions mismatch", failures)
        require(coverage_row.get("source_types") == matched_source_types, f"{coverage_prefix}: source_types mismatch", failures)
        require(coverage_row.get("display_component_ids") == source_display_ids, f"{coverage_prefix}: display ids mismatch", failures)
        require(coverage_row.get("blocked_numeric_component_ids") == source_blocked_ids, f"{coverage_prefix}: blocked ids mismatch", failures)
        require(coverage_row.get("numeric_total_status") == "blocked", f"{coverage_prefix}: numeric total status mismatch", failures)
        require(
            isinstance(coverage_row.get("safe_use"), str) and "do not close route-ready inputs" in coverage_row.get("safe_use"),
            f"{coverage_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(coverage_row.get("next_action"), str) and bool(coverage_row.get("next_action")), f"{coverage_prefix}: next_action missing", failures)

    route_ready_evidence_checklist = summary.get("route_ready_evidence_checklist")
    require(
        isinstance(route_ready_evidence_checklist, list) and bool(route_ready_evidence_checklist),
        "model.diagnostic_cost_estimate_v0.summary.route_ready_evidence_checklist: missing",
        failures,
    )

    def source_fields_for_components(component_ids):
        source_fields = []
        for source_field, source_components in expected_source_groups.items():
            if any(item.get("id") in component_ids for item in source_components):
                source_fields.append(source_field)
        return source_fields

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
            "policy_ids": expected_policy_ids,
            "blocked_outputs": ["fee_bps", "slippage_bps", "carry_bps", "estimated_cost_bps", "route_allowed"],
        },
        {
            "gate_id": "depth_freshness_evidence",
            "gate_label": "Depth Freshness Evidence",
            "required_input_ids": ["depth_or_impact_model"],
            "required_policy_inputs": ["depth_snapshot_timestamp", "max_depth_age_ms", "stale_depth_action"],
            "component_ids": ["lighter_top_order_depth", "aster_top_of_book_spread", "aster_depth_ladder"],
            "policy_ids": expected_policy_ids,
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
            "policy_ids": expected_policy_ids,
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
    evidence_gate_ids = [
        item.get("gate_id")
        for item in route_ready_evidence_checklist
        if isinstance(item, dict)
    ] if isinstance(route_ready_evidence_checklist, list) else []
    require(
        evidence_gate_ids == [item["gate_id"] for item in expected_evidence],
        "model.diagnostic_cost_estimate_v0.summary.route_ready_evidence_checklist: gate order mismatch",
        failures,
    )
    for evidence_row, expected in zip(route_ready_evidence_checklist if isinstance(route_ready_evidence_checklist, list) else [], expected_evidence):
        if not isinstance(evidence_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.route_ready_evidence_checklist: row must be object")
            continue
        evidence_prefix = f"model.diagnostic_cost_estimate_v0.summary.route_ready_evidence_checklist.{evidence_row.get('gate_id')}"
        expected_source_fields = source_fields_for_components(expected["component_ids"])
        require(evidence_row.get("gate_label") == expected["gate_label"], f"{evidence_prefix}: gate label mismatch", failures)
        require(evidence_row.get("status") == "evidence_required", f"{evidence_prefix}: status mismatch", failures)
        require(evidence_row.get("required_input_ids") == expected["required_input_ids"], f"{evidence_prefix}: required inputs mismatch", failures)
        require(evidence_row.get("required_policy_inputs") == expected["required_policy_inputs"], f"{evidence_prefix}: required policy inputs mismatch", failures)
        require(evidence_row.get("component_ids") == expected["component_ids"], f"{evidence_prefix}: component ids mismatch", failures)
        require(evidence_row.get("policy_ids") == expected["policy_ids"], f"{evidence_prefix}: policy ids mismatch", failures)
        require(evidence_row.get("source_field_ids") == expected_source_fields, f"{evidence_prefix}: source fields mismatch", failures)
        require(evidence_row.get("blocked_outputs") == expected["blocked_outputs"], f"{evidence_prefix}: blocked outputs mismatch", failures)
        require(evidence_row.get("evidence_count") == len(expected_source_fields), f"{evidence_prefix}: evidence count mismatch", failures)
        require(evidence_row.get("numeric_total_status") == "blocked", f"{evidence_prefix}: numeric total status mismatch", failures)
        require(evidence_row.get("may_estimate_cost_bps") is False, f"{evidence_prefix}: cost bps must stay blocked", failures)
        require(evidence_row.get("may_rank_routes") is False, f"{evidence_prefix}: route ranking must stay blocked", failures)
        require(evidence_row.get("may_submit_orders") is False, f"{evidence_prefix}: execution must stay blocked", failures)
        require(
            isinstance(evidence_row.get("safe_use"), str) and "do not estimate route cost" in evidence_row.get("safe_use"),
            f"{evidence_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(evidence_row.get("next_action"), str) and bool(evidence_row.get("next_action")), f"{evidence_prefix}: next_action missing", failures)

    evidence_by_gate_id = {
        item.get("gate_id"): item
        for item in route_ready_evidence_checklist
        if isinstance(item, dict) and item.get("gate_id")
    } if isinstance(route_ready_evidence_checklist, list) else {}

    def evidence_values(gate_ids, key):
        values = []
        for gate_id in gate_ids:
            gate = evidence_by_gate_id.get(gate_id, {})
            gate_values = gate.get(key) if isinstance(gate.get(key), list) else []
            for value in gate_values:
                if value not in values:
                    values.append(value)
        return values

    expected_gmx_diagnostic_fields = [
        "rate_semantics_status",
        "rate_relation_diagnostics",
        "rate_relation_summary",
        "rate_source_fields_status",
        "rate_source_fields_summary",
    ]
    expected_gmx_fixture_ids = [
        "net_rate_relation_raw_fields",
        "live_nonzero_borrowing_raw_sum_relation_observed",
        "live_zero_borrowing_relation_ambiguity",
        "live_shape_offline_fixture",
    ]
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
            "diagnostic_field_ids": expected_gmx_diagnostic_fields,
            "fixture_coverage_ids": expected_gmx_fixture_ids,
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
    venue_evidence_status = summary.get("venue_evidence_status")
    require(
        isinstance(venue_evidence_status, list) and bool(venue_evidence_status),
        "model.diagnostic_cost_estimate_v0.summary.venue_evidence_status: missing",
        failures,
    )
    venue_evidence_ids = [
        item.get("venue_id")
        for item in venue_evidence_status
        if isinstance(item, dict)
    ] if isinstance(venue_evidence_status, list) else []
    require(
        venue_evidence_ids == [item["venue_id"] for item in expected_venue_evidence],
        "model.diagnostic_cost_estimate_v0.summary.venue_evidence_status: venue order mismatch",
        failures,
    )
    for venue_row, expected in zip(venue_evidence_status if isinstance(venue_evidence_status, list) else [], expected_venue_evidence):
        if not isinstance(venue_row, dict):
            failures.append("model.diagnostic_cost_estimate_v0.summary.venue_evidence_status: row must be object")
            continue
        venue_prefix = f"model.diagnostic_cost_estimate_v0.summary.venue_evidence_status.{venue_row.get('venue_id')}"
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
        require(venue_row.get("venue_label") == expected["venue_label"], f"{venue_prefix}: label mismatch", failures)
        require(venue_row.get("venue_scope") == expected["venue_scope"], f"{venue_prefix}: scope mismatch", failures)
        require(venue_row.get("status") == expected["status"], f"{venue_prefix}: status mismatch", failures)
        require(venue_row.get("venue_gate_ids") == expected["venue_gate_ids"], f"{venue_prefix}: venue gate ids mismatch", failures)
        require(venue_row.get("cross_venue_gate_ids") == expected["cross_venue_gate_ids"], f"{venue_prefix}: cross gate ids mismatch", failures)
        require(venue_row.get("required_input_ids") == expected_required_inputs, f"{venue_prefix}: required inputs mismatch", failures)
        require(venue_row.get("required_policy_inputs") == expected_policy_inputs, f"{venue_prefix}: policy inputs mismatch", failures)
        require(venue_row.get("component_ids") == expected["component_ids"], f"{venue_prefix}: component ids mismatch", failures)
        require(venue_row.get("policy_ids") == expected["policy_ids"], f"{venue_prefix}: policy ids mismatch", failures)
        require(venue_row.get("source_field_ids") == expected_source_fields, f"{venue_prefix}: source fields mismatch", failures)
        require(venue_row.get("diagnostic_field_ids") == expected["diagnostic_field_ids"], f"{venue_prefix}: diagnostic fields mismatch", failures)
        require(venue_row.get("fixture_coverage_ids") == expected["fixture_coverage_ids"], f"{venue_prefix}: fixture ids mismatch", failures)
        require(venue_row.get("blocked_outputs") == expected_blocked_outputs, f"{venue_prefix}: blocked outputs mismatch", failures)
        require(
            venue_row.get("evidence_count")
            == len(expected_source_fields) + len(expected["diagnostic_field_ids"]) + len(expected["fixture_coverage_ids"]),
            f"{venue_prefix}: evidence count mismatch",
            failures,
        )
        require(venue_row.get("numeric_total_status") == "blocked", f"{venue_prefix}: numeric total status mismatch", failures)
        require(venue_row.get("may_estimate_cost_bps") is False, f"{venue_prefix}: cost bps must stay blocked", failures)
        require(venue_row.get("may_rank_routes") is False, f"{venue_prefix}: route ranking must stay blocked", failures)
        require(venue_row.get("may_submit_orders") is False, f"{venue_prefix}: execution must stay blocked", failures)
        require(
            isinstance(venue_row.get("safe_use"), str) and "do not estimate route cost" in venue_row.get("safe_use"),
            f"{venue_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(venue_row.get("next_action"), str) and bool(venue_row.get("next_action")), f"{venue_prefix}: next_action missing", failures)


def require_gmx_rate_mapping_review(model, failures):
    review = model.get("gmx_rate_mapping_review_v0") if isinstance(model.get("gmx_rate_mapping_review_v0"), dict) else {}
    require(bool(review), "model.gmx_rate_mapping_review_v0: missing", failures)
    review_prefix = "model.gmx_rate_mapping_review_v0"
    expected_diagnostic_fields = [
        "rate_semantics_status",
        "rate_relation_diagnostics",
        "rate_relation_summary",
        "rate_source_fields_status",
        "rate_source_fields_summary",
    ]
    expected_source_inputs = [
        "fundingFactorPerSecond",
        "borrowingFactorPerSecondForLongs",
        "borrowingFactorPerSecondForShorts",
        "longsPayShorts",
    ]
    expected_fixture_ids = [
        "net_rate_relation_raw_fields",
        "live_nonzero_borrowing_raw_sum_relation_observed",
        "live_zero_borrowing_relation_ambiguity",
        "live_shape_offline_fixture",
    ]
    expected_blocked_outputs = ["carry_bps", "estimated_cost_bps", "net_edge_bps", "route_allowed"]
    require(review.get("status") == "mapping_review_required", f"{review_prefix}: status mismatch", failures)
    require(review.get("read_only") is True, f"{review_prefix}: read_only must stay true", failures)
    require(review.get("source_relation_status") == "source_relation_guardrail_added", f"{review_prefix}: source relation status mismatch", failures)
    require(review.get("live_mapping_status") == "source_vs_live_mapping_unresolved", f"{review_prefix}: live mapping status mismatch", failures)
    require(review.get("diagnostic_field_ids") == expected_diagnostic_fields, f"{review_prefix}: diagnostic fields mismatch", failures)
    require(review.get("source_inputs_required") == expected_source_inputs, f"{review_prefix}: source inputs mismatch", failures)
    require(review.get("fixture_coverage_ids") == expected_fixture_ids, f"{review_prefix}: fixture ids mismatch", failures)
    require(review.get("blocked_outputs") == expected_blocked_outputs, f"{review_prefix}: blocked outputs mismatch", failures)
    require(review.get("may_emit_carry_bps") is False, f"{review_prefix}: carry bps must stay blocked", failures)
    require(review.get("may_estimate_cost_bps") is False, f"{review_prefix}: cost bps must stay blocked", failures)
    require(review.get("may_rank_routes") is False, f"{review_prefix}: route ranking must stay blocked", failures)
    require(review.get("may_submit_orders") is False, f"{review_prefix}: execution must stay blocked", failures)
    require(
        isinstance(review.get("safe_use"), str) and "no percent, bps" in review.get("safe_use"),
        f"{review_prefix}: safe_use mismatch",
        failures,
    )
    require(isinstance(review.get("next_action"), str) and bool(review.get("next_action")), f"{review_prefix}: next_action missing", failures)
    review_items = review.get("review_items")
    require(isinstance(review_items, list) and bool(review_items), f"{review_prefix}.review_items: missing", failures)
    expected_review_ids = [
        "source_relation_guardrail",
        "live_nonzero_borrowing_mapping",
        "source_helper_inputs",
        "carry_conversion_boundary",
    ]
    review_ids = [
        item.get("review_id")
        for item in review_items
        if isinstance(item, dict)
    ] if isinstance(review_items, list) else []
    require(review_ids == expected_review_ids, f"{review_prefix}.review_items: id order mismatch", failures)
    expected_statuses = [
        "source_relation_guardrail_added",
        "mapping_review_required",
        "source_inputs_missing",
        "blocked_for_carry_conversion",
    ]
    for item, expected_status in zip(review_items if isinstance(review_items, list) else [], expected_statuses):
        if not isinstance(item, dict):
            failures.append(f"{review_prefix}.review_items: row must be object")
            continue
        item_prefix = f"{review_prefix}.review_items.{item.get('review_id')}"
        require(item.get("status") == expected_status, f"{item_prefix}: status mismatch", failures)
        require(isinstance(item.get("evidence_count"), int), f"{item_prefix}: evidence_count missing", failures)
        require(isinstance(item.get("diagnostic_field_ids"), list) and bool(item.get("diagnostic_field_ids")), f"{item_prefix}: diagnostic fields missing", failures)
        require(isinstance(item.get("source_inputs_required"), list), f"{item_prefix}: source inputs missing", failures)
        require(isinstance(item.get("fixture_coverage_ids"), list), f"{item_prefix}: fixture ids missing", failures)
        require(isinstance(item.get("blocked_by"), list), f"{item_prefix}: blockers missing", failures)
        require(item.get("blocked_outputs") == expected_blocked_outputs, f"{item_prefix}: blocked outputs mismatch", failures)
        require(
            isinstance(item.get("safe_use"), str) and "no percent, bps" in item.get("safe_use"),
            f"{item_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(item.get("next_action"), str) and bool(item.get("next_action")), f"{item_prefix}: next_action missing", failures)
    blocker_breakdown = review.get("blocker_breakdown")
    require(isinstance(blocker_breakdown, list) and bool(blocker_breakdown), f"{review_prefix}.blocker_breakdown: missing", failures)
    expected_blocker_ids = [
        "live_markets_info_nonzero_borrowing_rate_mapping_review",
        "broader_live_fixture_coverage_across_market_states",
        "live_markets_info_source_helper_inputs_unavailable",
        "side_aware_funding_sign_tests",
        "holding_period_hours_input",
        "position_notional_usd_input",
        "production_decision_on_hourly_vs_annualized_display",
    ]
    blocker_ids = [
        item.get("blocker_id")
        for item in blocker_breakdown
        if isinstance(item, dict)
    ] if isinstance(blocker_breakdown, list) else []
    require(blocker_ids == expected_blocker_ids, f"{review_prefix}.blocker_breakdown: id order mismatch", failures)
    for blocker in blocker_breakdown if isinstance(blocker_breakdown, list) else []:
        if not isinstance(blocker, dict):
            failures.append(f"{review_prefix}.blocker_breakdown: row must be object")
            continue
        blocker_prefix = f"{review_prefix}.blocker_breakdown.{blocker.get('blocker_id')}"
        require(isinstance(blocker.get("blocker"), str) and bool(blocker.get("blocker")), f"{blocker_prefix}: blocker text missing", failures)
        require(blocker.get("review_count") == len(blocker.get("review_ids") or []), f"{blocker_prefix}: review count mismatch", failures)
        require(isinstance(blocker.get("review_statuses"), list) and bool(blocker.get("review_statuses")), f"{blocker_prefix}: review statuses missing", failures)
        require(blocker.get("blocked_outputs") == expected_blocked_outputs, f"{blocker_prefix}: blocked outputs mismatch", failures)
        require(blocker.get("may_emit_carry_bps") is False, f"{blocker_prefix}: carry bps must stay blocked", failures)
        require(blocker.get("may_estimate_cost_bps") is False, f"{blocker_prefix}: cost bps must stay blocked", failures)
        require(blocker.get("may_rank_routes") is False, f"{blocker_prefix}: route ranking must stay blocked", failures)
        require(blocker.get("may_submit_orders") is False, f"{blocker_prefix}: execution must stay blocked", failures)
        require(
            isinstance(blocker.get("safe_use"), str) and "no percent, bps" in blocker.get("safe_use"),
            f"{blocker_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(blocker.get("next_action"), str) and bool(blocker.get("next_action")), f"{blocker_prefix}: next_action missing", failures)
    fixture_matrix = review.get("fixture_readiness_matrix")
    require(isinstance(fixture_matrix, list) and bool(fixture_matrix), f"{review_prefix}.fixture_readiness_matrix: missing", failures)
    expected_fixture_case_ids = [
        "source_relation_raw_fields",
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
        "source_helper_inputs_presence",
    ]
    fixture_case_ids = [
        item.get("case_id")
        for item in fixture_matrix
        if isinstance(item, dict)
    ] if isinstance(fixture_matrix, list) else []
    require(fixture_case_ids == expected_fixture_case_ids, f"{review_prefix}.fixture_readiness_matrix: case id order mismatch", failures)
    expected_fixture_statuses = [
        "offline_guardrail_added",
        "mapping_review_required",
        "relation_ambiguous",
        "fixture_required",
        "source_inputs_missing",
    ]
    for fixture_case, expected_status in zip(fixture_matrix if isinstance(fixture_matrix, list) else [], expected_fixture_statuses):
        if not isinstance(fixture_case, dict):
            failures.append(f"{review_prefix}.fixture_readiness_matrix: row must be object")
            continue
        fixture_prefix = f"{review_prefix}.fixture_readiness_matrix.{fixture_case.get('case_id')}"
        require(fixture_case.get("status") == expected_status, f"{fixture_prefix}: status mismatch", failures)
        require(isinstance(fixture_case.get("case_label"), str) and bool(fixture_case.get("case_label")), f"{fixture_prefix}: case label missing", failures)
        require(isinstance(fixture_case.get("evidence_count"), int), f"{fixture_prefix}: evidence_count missing", failures)
        require(isinstance(fixture_case.get("diagnostic_field_ids"), list) and bool(fixture_case.get("diagnostic_field_ids")), f"{fixture_prefix}: diagnostic fields missing", failures)
        require(isinstance(fixture_case.get("source_inputs_required"), list), f"{fixture_prefix}: source inputs missing", failures)
        require(isinstance(fixture_case.get("fixture_coverage_ids"), list), f"{fixture_prefix}: fixture ids missing", failures)
        require(isinstance(fixture_case.get("expectation_ids", []), list), f"{fixture_prefix}: expectation ids mismatch", failures)
        require(isinstance(fixture_case.get("expectation_notes", []), list), f"{fixture_prefix}: expectation notes mismatch", failures)
        require(isinstance(fixture_case.get("blocked_by"), list) and bool(fixture_case.get("blocked_by")), f"{fixture_prefix}: blockers missing", failures)
        require(fixture_case.get("blocked_outputs") == expected_blocked_outputs, f"{fixture_prefix}: blocked outputs mismatch", failures)
        require(fixture_case.get("may_emit_carry_bps") is False, f"{fixture_prefix}: carry bps must stay blocked", failures)
        require(
            isinstance(fixture_case.get("safe_use"), str) and "no percent, bps" in fixture_case.get("safe_use"),
            f"{fixture_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(fixture_case.get("next_action"), str) and bool(fixture_case.get("next_action")), f"{fixture_prefix}: next_action missing", failures)
    expected_expectation_ids = [
        "long_position_pays_when_longs_pay_shorts_true",
        "short_position_receives_when_longs_pay_shorts_true",
        "short_position_pays_when_longs_pay_shorts_false",
        "long_position_receives_when_longs_pay_shorts_false",
    ]
    if isinstance(fixture_matrix, list):
        fixture_by_id = {
            item.get("case_id"): item
            for item in fixture_matrix
            if isinstance(item, dict)
        }
        longs_pay_shorts_case = fixture_by_id.get("longs_pay_shorts_direction", {})
        require(
            longs_pay_shorts_case.get("expectation_ids") == expected_expectation_ids,
            f"{review_prefix}.fixture_readiness_matrix.longs_pay_shorts_direction: expectation ids mismatch",
            failures,
        )
        require(
            len(longs_pay_shorts_case.get("expectation_notes") or []) == len(expected_expectation_ids),
            f"{review_prefix}.fixture_readiness_matrix.longs_pay_shorts_direction: expectation notes mismatch",
            failures,
        )
    side_expectations = review.get("side_aware_fixture_expectations")
    require(isinstance(side_expectations, list) and bool(side_expectations), f"{review_prefix}.side_aware_fixture_expectations: missing", failures)
    expectation_ids = [
        item.get("expectation_id")
        for item in side_expectations
        if isinstance(item, dict)
    ] if isinstance(side_expectations, list) else []
    require(expectation_ids == expected_expectation_ids, f"{review_prefix}.side_aware_fixture_expectations: id order mismatch", failures)
    for expectation in side_expectations if isinstance(side_expectations, list) else []:
        if not isinstance(expectation, dict):
            failures.append(f"{review_prefix}.side_aware_fixture_expectations: row must be object")
            continue
        expectation_prefix = f"{review_prefix}.side_aware_fixture_expectations.{expectation.get('expectation_id')}"
        require(expectation.get("case_id") == "longs_pay_shorts_direction", f"{expectation_prefix}: case id mismatch", failures)
        require(expectation.get("status") == "fixture_required", f"{expectation_prefix}: status mismatch", failures)
        require(expectation.get("position_side") in ("long", "short"), f"{expectation_prefix}: side mismatch", failures)
        require(isinstance(expectation.get("longs_pay_shorts"), bool), f"{expectation_prefix}: longs_pay_shorts mismatch", failures)
        require(expectation.get("expected_funding_direction") in ("pay", "receive"), f"{expectation_prefix}: direction mismatch", failures)
        require(expectation.get("required_source_inputs") == ["fundingFactorPerSecond", "longsPayShorts"], f"{expectation_prefix}: source inputs mismatch", failures)
        require(expectation.get("blocked_outputs") == expected_blocked_outputs, f"{expectation_prefix}: blocked outputs mismatch", failures)
        require(expectation.get("may_emit_carry_bps") is False, f"{expectation_prefix}: carry bps must stay blocked", failures)
        require(
            isinstance(expectation.get("safe_use"), str) and "no percent, bps" in expectation.get("safe_use"),
            f"{expectation_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(expectation.get("next_action"), str) and bool(expectation.get("next_action")), f"{expectation_prefix}: next_action missing", failures)
    decision_checklist = review.get("mapping_decision_checklist")
    require(isinstance(decision_checklist, list) and bool(decision_checklist), f"{review_prefix}.mapping_decision_checklist: missing", failures)
    expected_decision_check_ids = [
        "source_helper_inputs_available",
        "nonzero_borrowing_relation_reviewed",
        "side_aware_direction_fixtures",
        "carry_inputs_defined",
        "display_unit_decision_recorded",
    ]
    decision_check_ids = [
        item.get("check_id")
        for item in decision_checklist
        if isinstance(item, dict)
    ] if isinstance(decision_checklist, list) else []
    require(decision_check_ids == expected_decision_check_ids, f"{review_prefix}.mapping_decision_checklist: id order mismatch", failures)
    expected_decision_statuses = [
        "source_inputs_missing",
        "mapping_review_required",
        "fixture_required",
        "input_required",
        "policy_input_required",
    ]
    expected_decision_manual_approval_ids = [
        "gmx_source_helper_input_review",
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_side_aware_sign_review",
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    decision_manual_approval_ids = [
        item.get("manual_approval_id")
        for item in decision_checklist
        if isinstance(item, dict)
    ] if isinstance(decision_checklist, list) else []
    require(
        decision_manual_approval_ids == expected_decision_manual_approval_ids,
        f"{review_prefix}.mapping_decision_checklist: manual approval id order mismatch",
        failures,
    )
    for check, expected_status in zip(decision_checklist if isinstance(decision_checklist, list) else [], expected_decision_statuses):
        if not isinstance(check, dict):
            failures.append(f"{review_prefix}.mapping_decision_checklist: row must be object")
            continue
        check_prefix = f"{review_prefix}.mapping_decision_checklist.{check.get('check_id')}"
        require(check.get("status") == expected_status, f"{check_prefix}: status mismatch", failures)
        require(isinstance(check.get("required_source_inputs"), list), f"{check_prefix}: source inputs missing", failures)
        require(isinstance(check.get("required_fixture_case_ids"), list), f"{check_prefix}: fixture case ids missing", failures)
        require(isinstance(check.get("required_expectation_ids"), list), f"{check_prefix}: expectation ids missing", failures)
        require(isinstance(check.get("required_review_ids"), list) and bool(check.get("required_review_ids")), f"{check_prefix}: review ids missing", failures)
        require(check.get("manual_approval_required") is True, f"{check_prefix}: manual approval must stay required", failures)
        require(isinstance(check.get("manual_approval_id"), str) and bool(check.get("manual_approval_id")), f"{check_prefix}: manual approval id missing", failures)
        require(check.get("blocked_outputs") == expected_blocked_outputs, f"{check_prefix}: blocked outputs mismatch", failures)
        require(check.get("may_emit_carry_bps") is False, f"{check_prefix}: carry bps must stay blocked", failures)
        require(check.get("may_estimate_cost_bps") is False, f"{check_prefix}: cost bps must stay blocked", failures)
        require(check.get("may_rank_routes") is False, f"{check_prefix}: route ranking must stay blocked", failures)
        require(check.get("may_submit_orders") is False, f"{check_prefix}: execution must stay blocked", failures)
        require(
            isinstance(check.get("safe_use"), str) and "no percent, bps" in check.get("safe_use"),
            f"{check_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(check.get("next_action"), str) and bool(check.get("next_action")), f"{check_prefix}: next_action missing", failures)
    carry_summary = review.get("carry_readiness_summary")
    require(isinstance(carry_summary, dict) and bool(carry_summary), f"{review_prefix}.carry_readiness_summary: missing", failures)
    if isinstance(carry_summary, dict):
        summary_prefix = f"{review_prefix}.carry_readiness_summary"
        require(carry_summary.get("status") == "blocked_for_diagnostic_carry_bps", f"{summary_prefix}: status mismatch", failures)
        require(carry_summary.get("input_count") == 5, f"{summary_prefix}: input count mismatch", failures)
        require(carry_summary.get("blocked_input_count") == 5, f"{summary_prefix}: blocked input count mismatch", failures)
        require(carry_summary.get("manual_approval_count") == 5, f"{summary_prefix}: manual approval count mismatch", failures)
        require(
            sorted(carry_summary.get("required_source_inputs") or []) == sorted(expected_source_inputs),
            f"{summary_prefix}: required source inputs mismatch",
            failures,
        )
        require(
            carry_summary.get("required_fixture_case_ids") == [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
                "source_helper_inputs_presence",
            ],
            f"{summary_prefix}: required fixture case ids mismatch",
            failures,
        )
        require(carry_summary.get("required_expectation_ids") == expected_expectation_ids, f"{summary_prefix}: expectation ids mismatch", failures)
        require(
            sorted(carry_summary.get("required_decision_check_ids") or []) == sorted(expected_decision_check_ids),
            f"{summary_prefix}: required decision check ids mismatch",
            failures,
        )
        require(
            carry_summary.get("required_manual_approval_ids") == expected_decision_manual_approval_ids,
            f"{summary_prefix}: manual approval ids mismatch",
            failures,
        )
        require(carry_summary.get("blocked_outputs") == expected_blocked_outputs, f"{summary_prefix}: blocked outputs mismatch", failures)
        require(carry_summary.get("may_emit_carry_bps") is False, f"{summary_prefix}: carry bps must stay blocked", failures)
        require(carry_summary.get("may_estimate_cost_bps") is False, f"{summary_prefix}: cost bps must stay blocked", failures)
        require(carry_summary.get("may_rank_routes") is False, f"{summary_prefix}: route ranking must stay blocked", failures)
        require(carry_summary.get("may_submit_orders") is False, f"{summary_prefix}: execution must stay blocked", failures)
        require(
            isinstance(carry_summary.get("safe_use"), str) and "no percent, bps" in carry_summary.get("safe_use"),
            f"{summary_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(carry_summary.get("next_action"), str) and bool(carry_summary.get("next_action")), f"{summary_prefix}: next_action missing", failures)
    carry_checklist = review.get("carry_input_checklist")
    require(isinstance(carry_checklist, list) and bool(carry_checklist), f"{review_prefix}.carry_input_checklist: missing", failures)
    expected_carry_input_ids = [
        "holding_period_hours",
        "position_notional_usd",
        "rate_sign_convention",
        "source_helper_inputs",
        "display_unit_decision",
    ]
    expected_carry_statuses = [
        "input_required",
        "input_required",
        "fixture_required",
        "source_inputs_missing",
        "policy_input_required",
    ]
    carry_input_ids = [
        item.get("input_id")
        for item in carry_checklist
        if isinstance(item, dict)
    ] if isinstance(carry_checklist, list) else []
    require(carry_input_ids == expected_carry_input_ids, f"{review_prefix}.carry_input_checklist: input id order mismatch", failures)
    for carry_input, expected_status in zip(carry_checklist if isinstance(carry_checklist, list) else [], expected_carry_statuses):
        if not isinstance(carry_input, dict):
            failures.append(f"{review_prefix}.carry_input_checklist: row must be object")
            continue
        carry_prefix = f"{review_prefix}.carry_input_checklist.{carry_input.get('input_id')}"
        require(carry_input.get("status") == expected_status, f"{carry_prefix}: status mismatch", failures)
        require(isinstance(carry_input.get("input_label"), str) and bool(carry_input.get("input_label")), f"{carry_prefix}: input label missing", failures)
        require(isinstance(carry_input.get("input_type"), str) and bool(carry_input.get("input_type")), f"{carry_prefix}: input type missing", failures)
        require(isinstance(carry_input.get("required_source_inputs"), list), f"{carry_prefix}: source inputs missing", failures)
        require(isinstance(carry_input.get("required_fixture_case_ids"), list), f"{carry_prefix}: fixture case ids missing", failures)
        require(isinstance(carry_input.get("required_expectation_ids"), list), f"{carry_prefix}: expectation ids missing", failures)
        require(isinstance(carry_input.get("required_decision_check_ids"), list) and bool(carry_input.get("required_decision_check_ids")), f"{carry_prefix}: decision check ids missing", failures)
        require(carry_input.get("manual_approval_required") is True, f"{carry_prefix}: manual approval must stay required", failures)
        require(isinstance(carry_input.get("manual_approval_id"), str) and bool(carry_input.get("manual_approval_id")), f"{carry_prefix}: manual approval id missing", failures)
        require(isinstance(carry_input.get("blocked_by"), list) and bool(carry_input.get("blocked_by")), f"{carry_prefix}: blockers missing", failures)
        require(carry_input.get("blocked_outputs") == expected_blocked_outputs, f"{carry_prefix}: blocked outputs mismatch", failures)
        require(carry_input.get("may_emit_carry_bps") is False, f"{carry_prefix}: carry bps must stay blocked", failures)
        require(carry_input.get("may_estimate_cost_bps") is False, f"{carry_prefix}: cost bps must stay blocked", failures)
        require(carry_input.get("may_rank_routes") is False, f"{carry_prefix}: route ranking must stay blocked", failures)
        require(carry_input.get("may_submit_orders") is False, f"{carry_prefix}: execution must stay blocked", failures)
        require(
            isinstance(carry_input.get("safe_use"), str) and "no percent, bps" in carry_input.get("safe_use"),
            f"{carry_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(carry_input.get("next_action"), str) and bool(carry_input.get("next_action")), f"{carry_prefix}: next_action missing", failures)
    carry_evidence_summary = review.get("carry_source_evidence_summary")
    require(isinstance(carry_evidence_summary, dict) and bool(carry_evidence_summary), f"{review_prefix}.carry_source_evidence_summary: missing", failures)
    expected_carry_evidence_ids = [
        "holding_period_runtime_input",
        "position_notional_runtime_input",
        "side_aware_sign_fixture_evidence",
        "source_helper_field_evidence",
        "display_unit_policy_evidence",
        "carry_manual_approval_evidence",
    ]
    expected_carry_evidence_types = [
        "runtime_input",
        "runtime_input",
        "fixture_case",
        "source_field",
        "policy_decision",
        "manual_approval",
    ]
    expected_carry_evidence_statuses = [
        "input_required",
        "input_required",
        "fixture_required",
        "source_inputs_missing",
        "policy_input_required",
        "manual_approval_required",
    ]
    if isinstance(carry_evidence_summary, dict):
        evidence_summary_prefix = f"{review_prefix}.carry_source_evidence_summary"
        require(carry_evidence_summary.get("status") == "evidence_required", f"{evidence_summary_prefix}: status mismatch", failures)
        require(carry_evidence_summary.get("evidence_count") == 6, f"{evidence_summary_prefix}: evidence count mismatch", failures)
        require(carry_evidence_summary.get("blocked_evidence_count") == 6, f"{evidence_summary_prefix}: blocked evidence count mismatch", failures)
        require(carry_evidence_summary.get("evidence_ids") == expected_carry_evidence_ids, f"{evidence_summary_prefix}: evidence ids mismatch", failures)
        require(
            carry_evidence_summary.get("evidence_type_ids") == ["runtime_input", "fixture_case", "source_field", "policy_decision", "manual_approval"],
            f"{evidence_summary_prefix}: evidence type ids mismatch",
            failures,
        )
        require(carry_evidence_summary.get("input_ids") == expected_carry_input_ids, f"{evidence_summary_prefix}: input ids mismatch", failures)
        require(
            sorted(carry_evidence_summary.get("required_source_inputs") or []) == sorted(expected_source_inputs),
            f"{evidence_summary_prefix}: required source inputs mismatch",
            failures,
        )
        require(
            carry_evidence_summary.get("required_fixture_case_ids") == [
                "source_relation_raw_fields",
                "longs_pay_shorts_direction",
                "live_nonzero_borrowing_relation",
                "live_zero_borrowing_ambiguity",
                "source_helper_inputs_presence",
            ],
            f"{evidence_summary_prefix}: fixture ids mismatch",
            failures,
        )
        require(carry_evidence_summary.get("required_expectation_ids") == expected_expectation_ids, f"{evidence_summary_prefix}: expectation ids mismatch", failures)
        require(
            sorted(carry_evidence_summary.get("required_decision_check_ids") or []) == sorted(expected_decision_check_ids),
            f"{evidence_summary_prefix}: decision check ids mismatch",
            failures,
        )
        require(carry_evidence_summary.get("required_manual_approval_ids") == expected_decision_manual_approval_ids, f"{evidence_summary_prefix}: manual approval ids mismatch", failures)
        require(carry_evidence_summary.get("blocked_outputs") == expected_blocked_outputs, f"{evidence_summary_prefix}: blocked outputs mismatch", failures)
        require(carry_evidence_summary.get("may_emit_carry_bps") is False, f"{evidence_summary_prefix}: carry bps must stay blocked", failures)
        require(carry_evidence_summary.get("may_estimate_cost_bps") is False, f"{evidence_summary_prefix}: cost bps must stay blocked", failures)
        require(carry_evidence_summary.get("may_rank_routes") is False, f"{evidence_summary_prefix}: route ranking must stay blocked", failures)
        require(carry_evidence_summary.get("may_submit_orders") is False, f"{evidence_summary_prefix}: execution must stay blocked", failures)
        require(
            isinstance(carry_evidence_summary.get("safe_use"), str) and "no percent, bps" in carry_evidence_summary.get("safe_use"),
            f"{evidence_summary_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(carry_evidence_summary.get("next_action"), str) and bool(carry_evidence_summary.get("next_action")), f"{evidence_summary_prefix}: next_action missing", failures)
    carry_evidence_checklist = review.get("carry_source_evidence_checklist")
    require(isinstance(carry_evidence_checklist, list) and bool(carry_evidence_checklist), f"{review_prefix}.carry_source_evidence_checklist: missing", failures)
    carry_evidence_ids = [
        item.get("evidence_id")
        for item in carry_evidence_checklist
        if isinstance(item, dict)
    ] if isinstance(carry_evidence_checklist, list) else []
    require(carry_evidence_ids == expected_carry_evidence_ids, f"{review_prefix}.carry_source_evidence_checklist: evidence id order mismatch", failures)
    for evidence, expected_status, expected_type in zip(
        carry_evidence_checklist if isinstance(carry_evidence_checklist, list) else [],
        expected_carry_evidence_statuses,
        expected_carry_evidence_types,
    ):
        if not isinstance(evidence, dict):
            failures.append(f"{review_prefix}.carry_source_evidence_checklist: row must be object")
            continue
        evidence_prefix = f"{review_prefix}.carry_source_evidence_checklist.{evidence.get('evidence_id')}"
        require(evidence.get("status") == expected_status, f"{evidence_prefix}: status mismatch", failures)
        require(evidence.get("evidence_type") == expected_type, f"{evidence_prefix}: evidence type mismatch", failures)
        require(isinstance(evidence.get("evidence_label"), str) and bool(evidence.get("evidence_label")), f"{evidence_prefix}: evidence label missing", failures)
        require(isinstance(evidence.get("related_input_ids"), list) and bool(evidence.get("related_input_ids")), f"{evidence_prefix}: related input ids missing", failures)
        require(isinstance(evidence.get("required_source_inputs"), list), f"{evidence_prefix}: source inputs missing", failures)
        require(isinstance(evidence.get("required_fixture_case_ids"), list), f"{evidence_prefix}: fixture case ids missing", failures)
        require(isinstance(evidence.get("required_expectation_ids"), list), f"{evidence_prefix}: expectation ids missing", failures)
        require(isinstance(evidence.get("required_decision_check_ids"), list) and bool(evidence.get("required_decision_check_ids")), f"{evidence_prefix}: decision check ids missing", failures)
        require(isinstance(evidence.get("required_manual_approval_ids"), list) and bool(evidence.get("required_manual_approval_ids")), f"{evidence_prefix}: manual approval ids missing", failures)
        require(isinstance(evidence.get("blocked_by"), list) and bool(evidence.get("blocked_by")), f"{evidence_prefix}: blockers missing", failures)
        require(evidence.get("blocked_outputs") == expected_blocked_outputs, f"{evidence_prefix}: blocked outputs mismatch", failures)
        require(evidence.get("may_emit_carry_bps") is False, f"{evidence_prefix}: carry bps must stay blocked", failures)
        require(evidence.get("may_estimate_cost_bps") is False, f"{evidence_prefix}: cost bps must stay blocked", failures)
        require(evidence.get("may_rank_routes") is False, f"{evidence_prefix}: route ranking must stay blocked", failures)
        require(evidence.get("may_submit_orders") is False, f"{evidence_prefix}: execution must stay blocked", failures)
        require(
            isinstance(evidence.get("safe_use"), str) and "no percent, bps" in evidence.get("safe_use"),
            f"{evidence_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(evidence.get("next_action"), str) and bool(evidence.get("next_action")), f"{evidence_prefix}: next_action missing", failures)
    live_helper_summary = review.get("live_helper_source_summary")
    require(isinstance(live_helper_summary, dict) and bool(live_helper_summary), f"{review_prefix}.live_helper_source_summary: missing", failures)
    expected_live_helper_review_ids = [
        "live_rate_output_fields_available",
        "nonzero_borrowing_relation_evidence",
        "helper_source_fields_presence",
        "side_direction_helper_fields",
        "manual_live_helper_mapping_review",
    ]
    expected_live_helper_statuses = [
        "raw_outputs_available",
        "mapping_review_required",
        "source_inputs_missing",
        "fixture_required",
        "manual_approval_required",
    ]
    expected_live_rate_output_fields = [
        "fundingRateLong",
        "fundingRateShort",
        "borrowingRateLong",
        "borrowingRateShort",
        "netRateLong",
        "netRateShort",
    ]
    expected_live_helper_manual_approval_ids = [
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_source_helper_input_review",
        "gmx_side_aware_sign_review",
        "gmx_live_helper_source_review",
    ]
    if isinstance(live_helper_summary, dict):
        helper_summary_prefix = f"{review_prefix}.live_helper_source_summary"
        require(live_helper_summary.get("status") == "helper_source_review_required", f"{helper_summary_prefix}: status mismatch", failures)
        require(live_helper_summary.get("review_count") == 5, f"{helper_summary_prefix}: review count mismatch", failures)
        require(live_helper_summary.get("blocked_review_count") == 5, f"{helper_summary_prefix}: blocked review count mismatch", failures)
        require(live_helper_summary.get("review_ids") == expected_live_helper_review_ids, f"{helper_summary_prefix}: review ids mismatch", failures)
        require(live_helper_summary.get("review_statuses") == expected_live_helper_statuses, f"{helper_summary_prefix}: review statuses mismatch", failures)
        require(live_helper_summary.get("observed_source_fields") == expected_live_rate_output_fields, f"{helper_summary_prefix}: observed source fields mismatch", failures)
        require(live_helper_summary.get("required_source_inputs") == expected_source_inputs, f"{helper_summary_prefix}: required source inputs mismatch", failures)
        require(live_helper_summary.get("present_source_inputs") == [], f"{helper_summary_prefix}: present source inputs mismatch", failures)
        require(live_helper_summary.get("missing_source_inputs") == expected_source_inputs, f"{helper_summary_prefix}: missing source inputs mismatch", failures)
        require(live_helper_summary.get("expectation_ids") == expected_expectation_ids, f"{helper_summary_prefix}: expectation ids mismatch", failures)
        require(live_helper_summary.get("manual_approval_ids") == expected_live_helper_manual_approval_ids, f"{helper_summary_prefix}: manual approval ids mismatch", failures)
        require(live_helper_summary.get("blocked_outputs") == expected_blocked_outputs, f"{helper_summary_prefix}: blocked outputs mismatch", failures)
        require(live_helper_summary.get("may_emit_carry_bps") is False, f"{helper_summary_prefix}: carry bps must stay blocked", failures)
        require(live_helper_summary.get("may_estimate_cost_bps") is False, f"{helper_summary_prefix}: cost bps must stay blocked", failures)
        require(live_helper_summary.get("may_rank_routes") is False, f"{helper_summary_prefix}: route ranking must stay blocked", failures)
        require(live_helper_summary.get("may_submit_orders") is False, f"{helper_summary_prefix}: execution must stay blocked", failures)
        require(
            isinstance(live_helper_summary.get("safe_use"), str) and "no percent, bps" in live_helper_summary.get("safe_use"),
            f"{helper_summary_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(live_helper_summary.get("next_action"), str) and bool(live_helper_summary.get("next_action")), f"{helper_summary_prefix}: next_action missing", failures)
    live_helper_checklist = review.get("live_helper_source_checklist")
    require(isinstance(live_helper_checklist, list) and bool(live_helper_checklist), f"{review_prefix}.live_helper_source_checklist: missing", failures)
    live_helper_ids = [
        item.get("review_id")
        for item in live_helper_checklist
        if isinstance(item, dict)
    ] if isinstance(live_helper_checklist, list) else []
    require(live_helper_ids == expected_live_helper_review_ids, f"{review_prefix}.live_helper_source_checklist: review id order mismatch", failures)
    for helper_review, expected_status in zip(live_helper_checklist if isinstance(live_helper_checklist, list) else [], expected_live_helper_statuses):
        if not isinstance(helper_review, dict):
            failures.append(f"{review_prefix}.live_helper_source_checklist: row must be object")
            continue
        helper_prefix = f"{review_prefix}.live_helper_source_checklist.{helper_review.get('review_id')}"
        require(helper_review.get("status") == expected_status, f"{helper_prefix}: status mismatch", failures)
        require(isinstance(helper_review.get("review_label"), str) and bool(helper_review.get("review_label")), f"{helper_prefix}: review label missing", failures)
        require(isinstance(helper_review.get("source_scope"), str) and bool(helper_review.get("source_scope")), f"{helper_prefix}: source scope missing", failures)
        require(isinstance(helper_review.get("evidence_count"), int), f"{helper_prefix}: evidence count missing", failures)
        require(isinstance(helper_review.get("observed_source_fields"), list), f"{helper_prefix}: observed source fields missing", failures)
        require(isinstance(helper_review.get("required_source_inputs"), list), f"{helper_prefix}: required source inputs missing", failures)
        require(isinstance(helper_review.get("present_source_inputs"), list), f"{helper_prefix}: present source inputs missing", failures)
        require(isinstance(helper_review.get("missing_source_inputs"), list), f"{helper_prefix}: missing source inputs missing", failures)
        require(isinstance(helper_review.get("diagnostic_field_ids"), list) and bool(helper_review.get("diagnostic_field_ids")), f"{helper_prefix}: diagnostic fields missing", failures)
        require(isinstance(helper_review.get("fixture_case_ids"), list) and bool(helper_review.get("fixture_case_ids")), f"{helper_prefix}: fixture case ids missing", failures)
        require(isinstance(helper_review.get("expectation_ids"), list), f"{helper_prefix}: expectation ids missing", failures)
        require(helper_review.get("manual_approval_required") is True, f"{helper_prefix}: manual approval must stay required", failures)
        require(isinstance(helper_review.get("manual_approval_id"), str) and bool(helper_review.get("manual_approval_id")), f"{helper_prefix}: manual approval id missing", failures)
        require(isinstance(helper_review.get("blocked_by"), list) and bool(helper_review.get("blocked_by")), f"{helper_prefix}: blockers missing", failures)
        require(helper_review.get("blocked_outputs") == expected_blocked_outputs, f"{helper_prefix}: blocked outputs mismatch", failures)
        require(helper_review.get("may_emit_carry_bps") is False, f"{helper_prefix}: carry bps must stay blocked", failures)
        require(helper_review.get("may_estimate_cost_bps") is False, f"{helper_prefix}: cost bps must stay blocked", failures)
        require(helper_review.get("may_rank_routes") is False, f"{helper_prefix}: route ranking must stay blocked", failures)
        require(helper_review.get("may_submit_orders") is False, f"{helper_prefix}: execution must stay blocked", failures)
        require(
            isinstance(helper_review.get("safe_use"), str) and "no percent, bps" in helper_review.get("safe_use"),
            f"{helper_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(helper_review.get("next_action"), str) and bool(helper_review.get("next_action")), f"{helper_prefix}: next_action missing", failures)
    helper_follow_up_summary = review.get("helper_source_follow_up_summary")
    require(isinstance(helper_follow_up_summary, dict) and bool(helper_follow_up_summary), f"{review_prefix}.helper_source_follow_up_summary: missing", failures)
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
    expected_helper_follow_up_input_ids = [
        "source_helper_inputs",
        "rate_sign_convention",
        "holding_period_hours",
        "position_notional_usd",
        "display_unit_decision",
    ]
    expected_helper_follow_up_review_ids = [
        "helper_source_fields_presence",
        "manual_live_helper_mapping_review",
        "live_rate_output_fields_available",
        "nonzero_borrowing_relation_evidence",
        "side_direction_helper_fields",
        "carry_conversion_boundary",
    ]
    expected_helper_follow_up_fixture_ids = [
        "source_helper_inputs_presence",
        "live_nonzero_borrowing_relation",
        "live_zero_borrowing_ambiguity",
        "longs_pay_shorts_direction",
        "source_relation_raw_fields",
    ]
    expected_helper_follow_up_decision_ids = [
        "source_helper_inputs_available",
        "nonzero_borrowing_relation_reviewed",
        "side_aware_direction_fixtures",
        "carry_inputs_defined",
        "display_unit_decision_recorded",
    ]
    expected_helper_follow_up_manual_approval_ids = [
        "gmx_source_helper_input_review",
        "gmx_live_helper_source_review",
        "gmx_live_nonzero_borrowing_mapping_review",
        "gmx_side_aware_sign_review",
        "gmx_carry_horizon_notional_review",
        "gmx_hourly_vs_annualized_display_decision",
    ]
    if isinstance(helper_follow_up_summary, dict):
        follow_up_summary_prefix = f"{review_prefix}.helper_source_follow_up_summary"
        require(helper_follow_up_summary.get("status") == "follow_up_required", f"{follow_up_summary_prefix}: status mismatch", failures)
        require(helper_follow_up_summary.get("follow_up_count") == 4, f"{follow_up_summary_prefix}: follow up count mismatch", failures)
        require(helper_follow_up_summary.get("blocked_follow_up_count") == 4, f"{follow_up_summary_prefix}: blocked follow up count mismatch", failures)
        require(helper_follow_up_summary.get("follow_up_ids") == expected_helper_follow_up_ids, f"{follow_up_summary_prefix}: follow up ids mismatch", failures)
        require(helper_follow_up_summary.get("follow_up_statuses") == expected_helper_follow_up_statuses, f"{follow_up_summary_prefix}: follow up statuses mismatch", failures)
        require(helper_follow_up_summary.get("related_input_ids") == expected_helper_follow_up_input_ids, f"{follow_up_summary_prefix}: related input ids mismatch", failures)
        require(helper_follow_up_summary.get("related_review_ids") == expected_helper_follow_up_review_ids, f"{follow_up_summary_prefix}: related review ids mismatch", failures)
        require(helper_follow_up_summary.get("missing_source_inputs") == expected_source_inputs, f"{follow_up_summary_prefix}: missing source inputs mismatch", failures)
        require(helper_follow_up_summary.get("required_fixture_case_ids") == expected_helper_follow_up_fixture_ids, f"{follow_up_summary_prefix}: fixture case ids mismatch", failures)
        require(helper_follow_up_summary.get("required_expectation_ids") == expected_expectation_ids, f"{follow_up_summary_prefix}: expectation ids mismatch", failures)
        require(helper_follow_up_summary.get("required_decision_check_ids") == expected_helper_follow_up_decision_ids, f"{follow_up_summary_prefix}: decision check ids mismatch", failures)
        require(helper_follow_up_summary.get("blocking_manual_approval_ids") == expected_helper_follow_up_manual_approval_ids, f"{follow_up_summary_prefix}: manual approval ids mismatch", failures)
        require(helper_follow_up_summary.get("blocked_outputs") == expected_blocked_outputs, f"{follow_up_summary_prefix}: blocked outputs mismatch", failures)
        require(helper_follow_up_summary.get("may_emit_carry_bps") is False, f"{follow_up_summary_prefix}: carry bps must stay blocked", failures)
        require(helper_follow_up_summary.get("may_estimate_cost_bps") is False, f"{follow_up_summary_prefix}: cost bps must stay blocked", failures)
        require(helper_follow_up_summary.get("may_rank_routes") is False, f"{follow_up_summary_prefix}: route ranking must stay blocked", failures)
        require(helper_follow_up_summary.get("may_submit_orders") is False, f"{follow_up_summary_prefix}: execution must stay blocked", failures)
        require(
            isinstance(helper_follow_up_summary.get("safe_use"), str) and "no percent, bps" in helper_follow_up_summary.get("safe_use"),
            f"{follow_up_summary_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(helper_follow_up_summary.get("next_action"), str) and bool(helper_follow_up_summary.get("next_action")), f"{follow_up_summary_prefix}: next_action missing", failures)
    helper_follow_up_checklist = review.get("helper_source_follow_up_checklist")
    require(isinstance(helper_follow_up_checklist, list) and bool(helper_follow_up_checklist), f"{review_prefix}.helper_source_follow_up_checklist: missing", failures)
    helper_follow_up_ids = [
        item.get("follow_up_id")
        for item in helper_follow_up_checklist
        if isinstance(item, dict)
    ] if isinstance(helper_follow_up_checklist, list) else []
    require(helper_follow_up_ids == expected_helper_follow_up_ids, f"{review_prefix}.helper_source_follow_up_checklist: follow up id order mismatch", failures)
    for follow_up, expected_status in zip(helper_follow_up_checklist if isinstance(helper_follow_up_checklist, list) else [], expected_helper_follow_up_statuses):
        if not isinstance(follow_up, dict):
            failures.append(f"{review_prefix}.helper_source_follow_up_checklist: row must be object")
            continue
        follow_up_prefix = f"{review_prefix}.helper_source_follow_up_checklist.{follow_up.get('follow_up_id')}"
        require(follow_up.get("status") == expected_status, f"{follow_up_prefix}: status mismatch", failures)
        require(isinstance(follow_up.get("follow_up_label"), str) and bool(follow_up.get("follow_up_label")), f"{follow_up_prefix}: label missing", failures)
        require(isinstance(follow_up.get("follow_up_type"), str) and bool(follow_up.get("follow_up_type")), f"{follow_up_prefix}: type missing", failures)
        require(isinstance(follow_up.get("related_input_ids"), list) and bool(follow_up.get("related_input_ids")), f"{follow_up_prefix}: related inputs missing", failures)
        require(isinstance(follow_up.get("related_review_ids"), list) and bool(follow_up.get("related_review_ids")), f"{follow_up_prefix}: related reviews missing", failures)
        require(isinstance(follow_up.get("missing_source_inputs"), list), f"{follow_up_prefix}: missing source inputs missing", failures)
        require(isinstance(follow_up.get("required_fixture_case_ids"), list), f"{follow_up_prefix}: fixture case ids missing", failures)
        require(isinstance(follow_up.get("required_expectation_ids"), list), f"{follow_up_prefix}: expectation ids missing", failures)
        require(isinstance(follow_up.get("required_decision_check_ids"), list) and bool(follow_up.get("required_decision_check_ids")), f"{follow_up_prefix}: decision check ids missing", failures)
        require(isinstance(follow_up.get("blocking_manual_approval_ids"), list) and bool(follow_up.get("blocking_manual_approval_ids")), f"{follow_up_prefix}: manual approvals missing", failures)
        require(isinstance(follow_up.get("blocked_by"), list) and bool(follow_up.get("blocked_by")), f"{follow_up_prefix}: blockers missing", failures)
        require(follow_up.get("blocked_outputs") == expected_blocked_outputs, f"{follow_up_prefix}: blocked outputs mismatch", failures)
        require(follow_up.get("may_emit_carry_bps") is False, f"{follow_up_prefix}: carry bps must stay blocked", failures)
        require(follow_up.get("may_estimate_cost_bps") is False, f"{follow_up_prefix}: cost bps must stay blocked", failures)
        require(follow_up.get("may_rank_routes") is False, f"{follow_up_prefix}: route ranking must stay blocked", failures)
        require(follow_up.get("may_submit_orders") is False, f"{follow_up_prefix}: execution must stay blocked", failures)
        require(
            isinstance(follow_up.get("safe_use"), str) and "no percent, bps" in follow_up.get("safe_use"),
            f"{follow_up_prefix}: safe_use mismatch",
            failures,
        )
        require(isinstance(follow_up.get("next_action"), str) and bool(follow_up.get("next_action")), f"{follow_up_prefix}: next_action missing", failures)


failures = []
summary = {"base_url": base_url, "endpoints": {}}

policy_status, policy_payload = fetch_json("/api/v1/perp-dex/route-constraints")
model_status, model_payload = fetch_json("/api/v1/perp-dex/route-model")

for name, status, payload in (
    ("route_constraints", policy_status, policy_payload),
    ("route_model", model_status, model_payload),
):
    summary["endpoints"][name] = {
        "http_status": status,
        "success": bool(payload.get("success")) if isinstance(payload, dict) else False,
        "detail": payload.get("detail") if isinstance(payload, dict) else None,
    }
    if status != 200 or not payload.get("success"):
        failures.append(f"{name}: request_failed")

policy = policy_payload.get("data") if isinstance(policy_payload, dict) else {}
policy = policy if isinstance(policy, dict) else {}
model = model_payload.get("data") if isinstance(model_payload, dict) else {}
model = model if isinstance(model, dict) else {}

policy_ui = policy.get("ui_policy") if isinstance(policy.get("ui_policy"), dict) else {}
model_output = model.get("output_policy") if isinstance(model.get("output_policy"), dict) else {}
diagnostics = model.get("diagnostic_cost_estimate_v0") if isinstance(model.get("diagnostic_cost_estimate_v0"), dict) else {}

summary["policy"] = {
    "status": policy.get("status"),
    "read_only": policy.get("read_only"),
    "execution_enabled": policy.get("execution_enabled"),
    "production_liquidity_signal": policy.get("production_liquidity_signal"),
    "may_rank_by_liquidity": policy_ui.get("may_rank_by_liquidity"),
    "may_submit_orders": policy_ui.get("may_submit_orders"),
    "blocker_ids": [item.get("id") for item in policy.get("blockers", []) if isinstance(item, dict)],
}
summary["model"] = {
    "status": model.get("status"),
    "read_only": model.get("read_only"),
    "execution_enabled": model.get("execution_enabled"),
    "ranking_enabled": model.get("ranking_enabled"),
    "production_signal_enabled": model.get("production_signal_enabled"),
    "may_estimate_cost_bps": model_output.get("may_estimate_cost_bps"),
    "may_rank_routes": model_output.get("may_rank_routes"),
    "may_submit_orders": model_output.get("may_submit_orders"),
    "may_emit_numeric_total_bps": diagnostics.get("may_emit_numeric_total_bps"),
    "required_input_ids": [item.get("id") for item in model.get("required_inputs", []) if isinstance(item, dict)],
    "formula_keys": sorted(model.get("formula_skeleton", {}).keys()) if isinstance(model.get("formula_skeleton"), dict) else [],
    "diagnostic_component_ids": [
        item.get("id")
        for item in diagnostics.get("components", [])
        if isinstance(item, dict)
    ] if isinstance(diagnostics.get("components"), list) else [],
    "display_component_ids": [
        item.get("id")
        for item in diagnostics.get("components", [])
        if isinstance(item, dict) and item.get("may_emit_component_bps") is True
    ] if isinstance(diagnostics.get("components"), list) else [],
    "diagnostic_component_summary": diagnostics.get("summary") if isinstance(diagnostics.get("summary"), dict) else {},
    "diagnostic_venue_breakdown": diagnostics.get("summary", {}).get("venue_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_blocker_breakdown": diagnostics.get("summary", {}).get("blocker_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_required_input_breakdown": diagnostics.get("summary", {}).get("required_input_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_source_field_breakdown": diagnostics.get("summary", {}).get("source_field_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_safe_use_breakdown": diagnostics.get("summary", {}).get("safe_use_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_readiness_rollup": diagnostics.get("summary", {}).get("readiness_rollup", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_depth_staleness_policy_checklist": diagnostics.get("summary", {}).get("depth_staleness_policy_checklist", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_required_policy_input_breakdown": diagnostics.get("summary", {}).get("required_policy_input_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_next_action_breakdown": diagnostics.get("summary", {}).get("next_action_breakdown", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_source_input_action_coverage": diagnostics.get("summary", {}).get("source_input_action_coverage", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_route_ready_evidence_checklist": diagnostics.get("summary", {}).get("route_ready_evidence_checklist", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "diagnostic_venue_evidence_status": diagnostics.get("summary", {}).get("venue_evidence_status", [])
    if isinstance(diagnostics.get("summary"), dict)
    else [],
    "gmx_rate_mapping_review": model.get("gmx_rate_mapping_review_v0", {})
    if isinstance(model.get("gmx_rate_mapping_review_v0"), dict)
    else {},
    "blocker_ids": [item.get("id") for item in model.get("blockers", []) if isinstance(item, dict)],
}
summary["contract"] = compact_contract(policy, model)

if compare_base_url:
    compare_policy_status, compare_policy_payload = fetch_json("/api/v1/perp-dex/route-constraints", compare_base_url)
    compare_model_status, compare_model_payload = fetch_json("/api/v1/perp-dex/route-model", compare_base_url)
    compare_policy = compare_policy_payload.get("data") if isinstance(compare_policy_payload, dict) else {}
    compare_policy = compare_policy if isinstance(compare_policy, dict) else {}
    compare_model = compare_model_payload.get("data") if isinstance(compare_model_payload, dict) else {}
    compare_model = compare_model if isinstance(compare_model, dict) else {}
    compare_contract = compact_contract(compare_policy, compare_model)
    contract_diffs = diff_contracts(summary["contract"], compare_contract)
    summary["compare"] = {
        "base_url": compare_base_url,
        "endpoints": {
            "route_constraints": {
                "http_status": compare_policy_status,
                "success": bool(compare_policy_payload.get("success")) if isinstance(compare_policy_payload, dict) else False,
                "detail": compare_policy_payload.get("detail") if isinstance(compare_policy_payload, dict) else None,
            },
            "route_model": {
                "http_status": compare_model_status,
                "success": bool(compare_model_payload.get("success")) if isinstance(compare_model_payload, dict) else False,
                "detail": compare_model_payload.get("detail") if isinstance(compare_model_payload, dict) else None,
            },
        },
        "contract": compare_contract,
        "diffs": contract_diffs,
    }
    if contract_diffs and fail_on_diff:
        failures.append("compare: contract_diff_detected")

require(policy.get("status") == "research_only", "policy: status must stay research_only", failures)
require(policy.get("read_only") is True, "policy: read_only must stay true", failures)
require(policy.get("execution_enabled") is False, "policy: execution_enabled must stay false", failures)
require(
    policy.get("production_liquidity_signal") is False,
    "policy: production_liquidity_signal must stay false",
    failures,
)
require(policy_ui.get("may_rank_by_liquidity") is False, "policy: may_rank_by_liquidity must stay false", failures)
require(policy_ui.get("may_submit_orders") is False, "policy: may_submit_orders must stay false", failures)
require_structured_blockers("policy.blockers", policy.get("blockers"), failures, require_scope=True)

require(model.get("status") == "inputs_required", "model: status must stay inputs_required", failures)
require(model.get("read_only") is True, "model: read_only must stay true", failures)
require(model.get("execution_enabled") is False, "model: execution_enabled must stay false", failures)
require(model.get("ranking_enabled") is False, "model: ranking_enabled must stay false", failures)
require(
    model.get("production_signal_enabled") is False,
    "model: production_signal_enabled must stay false",
    failures,
)
require(model_output.get("may_show_checklist") is True, "model: may_show_checklist must stay true", failures)
require(
    model_output.get("may_show_formula_skeleton") is True,
    "model: may_show_formula_skeleton must stay true",
    failures,
)
require(
    model_output.get("may_show_diagnostic_cost_components") is True,
    "model: may_show_diagnostic_cost_components must stay true",
    failures,
)
require(model_output.get("may_estimate_cost_bps") is False, "model: may_estimate_cost_bps must stay false", failures)
require(model_output.get("may_rank_routes") is False, "model: may_rank_routes must stay false", failures)
require(model_output.get("may_submit_orders") is False, "model: may_submit_orders must stay false", failures)
require(
    diagnostics.get("may_emit_numeric_total_bps") is False,
    "model: may_emit_numeric_total_bps must stay false",
    failures,
)
require_structured_blockers("model.blockers", model.get("blockers"), failures)
require_structured_required_inputs(model.get("required_inputs"), failures)
require_formula_skeleton(model.get("formula_skeleton"), failures)
require_diagnostic_components(diagnostics, model.get("required_inputs"), failures)
require_gmx_rate_mapping_review(model, failures)

print("ok")
print(json.dumps(summary, ensure_ascii=False, indent=2))

if failures and not allow_unavailable:
    raise SystemExit("; ".join(failures))
PY

printf 'Perp DEX policy smoke passed.\n'
