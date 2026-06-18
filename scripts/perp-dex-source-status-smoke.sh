#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
VENUES="${VENUES:-hyperliquid,dydx,lighter,aster,gmx}"
EXCHANGES="${EXCHANGES:-Aster,Lighter,EdgeX,Drift}"
MIN_TOTAL_ROWS="${MIN_TOTAL_ROWS:-1}"
MIN_MATCHED_EXCHANGES="${MIN_MATCHED_EXCHANGES:-1}"
ALLOW_UNAVAILABLE="${ALLOW_UNAVAILABLE:-0}"
RUN_COINGLASS="${RUN_COINGLASS:-1}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMPARE_BASE_URL="${COMPARE_BASE_URL:-}"
FAIL_ON_DIFF="${FAIL_ON_DIFF:-0}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Perp DEX source status smoke.\n' >&2
    exit 1
  fi
fi

printf 'Perp DEX source status smoke ... '
"$PYTHON_BIN" - "$BASE_URL" "$SYMBOLS" "$VENUES" "$EXCHANGES" "$MIN_TOTAL_ROWS" "$MIN_MATCHED_EXCHANGES" "$ALLOW_UNAVAILABLE" "$RUN_COINGLASS" "$TIMEOUT_SECONDS" "$COMPARE_BASE_URL" "$FAIL_ON_DIFF" <<'PY'
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

(
    base_url,
    symbols_raw,
    venues_raw,
    exchanges_raw,
    min_rows_raw,
    min_matched_raw,
    allow_raw,
    run_coinglass_raw,
    timeout_raw,
    compare_base_url,
    fail_on_diff_raw,
) = sys.argv[1:12]

base_url = base_url.rstrip("/")
compare_base_url = compare_base_url.rstrip("/") if compare_base_url else ""
symbols = [item.strip().upper() for item in symbols_raw.split(",") if item.strip()]
venues = [item.strip().lower() for item in venues_raw.split(",") if item.strip()]
exchanges = [item.strip() for item in exchanges_raw.split(",") if item.strip()]
min_total_rows = int(min_rows_raw)
min_matched_exchanges = int(min_matched_raw)
allow_unavailable = allow_raw == "1"
run_coinglass = run_coinglass_raw == "1"
timeout = int(timeout_raw)
fail_on_diff = fail_on_diff_raw == "1"

if not symbols:
    raise SystemExit("SYMBOLS must contain at least one symbol")
if not venues:
    raise SystemExit("VENUES must contain at least one direct venue")

known_provider_error_classes = {
    "timeout",
    "rate_limit",
    "empty_response",
    "schema_drift",
    "unavailable_endpoint",
    "provider_unavailable",
    "provider_http_error",
}


def fetch_json(path, root_url):
    request = Request(
        f"{root_url}{path}",
        headers={"Accept": "application/json", "User-Agent": "DeltaGridSmoke/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except Exception:
            return exc.code, {"success": False, "detail": str(exc)}
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, {"success": False, "detail": str(exc)}


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def bool_payload_success(payload):
    return bool(payload.get("success")) if isinstance(payload, dict) else False


def route_model_output_flags(model):
    output_policy = as_dict(model.get("output_policy"))
    diagnostics = as_dict(model.get("diagnostic_cost_estimate_v0"))
    return {
        "read_only": model.get("read_only"),
        "execution_enabled": model.get("execution_enabled"),
        "ranking_enabled": model.get("ranking_enabled"),
        "production_signal_enabled": model.get("production_signal_enabled"),
        "may_estimate_cost_bps": output_policy.get("may_estimate_cost_bps"),
        "may_rank_routes": output_policy.get("may_rank_routes"),
        "may_submit_orders": output_policy.get("may_submit_orders"),
        "may_emit_numeric_total_bps": diagnostics.get("may_emit_numeric_total_bps"),
    }


def diff_contracts(base_contract, compare_contract):
    diffs = []
    for field in sorted(set(base_contract) | set(compare_contract)):
        base_value = base_contract.get(field)
        compare_value = compare_contract.get(field)
        if base_value != compare_value:
            diffs.append({"field": field, "base": base_value, "compare": compare_value})
    return diffs


def compact_source_status(root_url):
    failures = []
    endpoints = {}
    direct_venues = {}
    total_direct_rows = 0
    depth_venue_ids = []
    normalized_venue_ids = [venue for venue in venues if venue != "gmx"]
    normalized_live_venue_ids = []
    direct_provider_error_classes = {}

    for venue in venues:
        query = urlencode({"symbols": ",".join(symbols)})
        status_code, payload = fetch_json(f"/api/v1/perp-dex/venues/{venue}/markets?{query}", root_url)
        payload = as_dict(payload)
        data = as_dict(payload.get("data"))
        detail = as_dict(payload.get("detail"))
        markets = as_list(data.get("markets"))
        availability = as_dict(data.get("availability_summary"))
        if not availability:
            availability = as_dict(detail.get("availability_summary"))
        provider_error_class = availability.get("provider_error_class") or detail.get("provider_error_class")
        depth_statuses = sorted(
            {
                str(row.get("orderbook_depth_status"))
                for row in markets
                if isinstance(row, dict) and row.get("orderbook_depth_status")
            }
        )
        depth_freshness = as_dict(as_dict(availability.get("depth_diagnostics")).get("freshness"))
        rows = len(markets)
        total_direct_rows += rows
        if depth_statuses:
            depth_venue_ids.append(venue)
        if venue in normalized_venue_ids and data.get("status") == "live" and rows > 0:
            normalized_live_venue_ids.append(venue)
        if provider_error_class:
            direct_provider_error_classes[venue] = provider_error_class

        direct_venues[venue] = {
            "http_status": status_code,
            "success": bool_payload_success(payload),
            "snapshot_status": data.get("status"),
            "availability_status": availability.get("status"),
            "provider_error_class": provider_error_class,
            "rows": rows,
            "read_only": data.get("read_only"),
            "availability_read_only": availability.get("read_only"),
            "execution_enabled": data.get("execution_enabled"),
            "availability_execution_enabled": availability.get("execution_enabled"),
            "ranking_enabled": data.get("ranking_enabled"),
            "availability_ranking_enabled": availability.get("ranking_enabled"),
            "production_signal_enabled": data.get("production_signal_enabled"),
            "availability_production_signal_enabled": availability.get("production_signal_enabled"),
            "normalization_status": data.get("normalization_status"),
            "matched_symbols": availability.get("matched_symbols") or [],
            "missing_symbols": availability.get("missing_symbols") or [],
            "depth_statuses": depth_statuses,
            "depth_freshness_status": depth_freshness.get("status"),
            "depth_freshness_numeric_total_status": depth_freshness.get("numeric_total_status"),
            "depth_freshness_may_emit_slippage_bps": depth_freshness.get("may_emit_slippage_bps"),
        }
        endpoints[f"direct_{venue}"] = {
            "http_status": status_code,
            "success": bool_payload_success(payload),
            "detail": payload.get("detail"),
        }

        if status_code != 200 or not bool_payload_success(payload):
            failures.append(f"{venue}: request_failed")
        if not availability:
            failures.append(f"{venue}: missing_availability_summary")
        if provider_error_class and provider_error_class not in known_provider_error_classes:
            failures.append(f"{venue}: unknown_provider_error_class:{provider_error_class}")
        if data.get("read_only") is not True:
            failures.append(f"{venue}: read_only_not_true")
        if data.get("execution_enabled") is not False:
            failures.append(f"{venue}: execution_enabled_true")
        if data.get("ranking_enabled") is True:
            failures.append(f"{venue}: ranking_enabled_true")
        if data.get("production_signal_enabled") is True:
            failures.append(f"{venue}: production_signal_enabled_true")
        if availability:
            if availability.get("read_only") is not True:
                failures.append(f"{venue}: availability_read_only_not_true")
            if availability.get("execution_enabled") is True:
                failures.append(f"{venue}: availability_execution_enabled_true")
            if availability.get("ranking_enabled") is True:
                failures.append(f"{venue}: availability_ranking_enabled_true")
            if availability.get("production_signal_enabled") is True:
                failures.append(f"{venue}: availability_production_signal_enabled_true")
            if depth_freshness:
                if depth_freshness.get("may_emit_slippage_bps") is not False:
                    failures.append(f"{venue}: depth_freshness_slippage_enabled")
                if depth_freshness.get("numeric_total_status") != "blocked":
                    failures.append(f"{venue}: depth_freshness_numeric_total_not_blocked")

    coinglass = {
        "enabled": run_coinglass,
        "http_status": None,
        "success": False,
        "status": "skipped",
        "rows": 0,
        "exchanges_with_matches": 0,
        "candidate_hints": [],
        "by_exchange_statuses": {},
        "by_exchange_route_input_statuses": {},
        "read_only": None,
        "execution_enabled": None,
        "ranking_enabled": None,
        "production_signal_enabled": None,
    }
    if run_coinglass:
        query = urlencode({"symbols": ",".join(symbols), "exchanges": ",".join(exchanges)})
        status_code, payload = fetch_json(f"/api/v1/perp-dex/venues/coinglass/markets?{query}", root_url)
        payload = as_dict(payload)
        data = as_dict(payload.get("data"))
        coverage = as_dict(data.get("coverage_summary"))
        by_exchange = as_dict(coverage.get("by_exchange"))
        rows = int(coverage.get("total_rows") or 0)
        matched_exchanges = int(coverage.get("exchanges_with_matches") or 0)
        coinglass = {
            "enabled": True,
            "http_status": status_code,
            "success": bool_payload_success(payload),
            "status": data.get("status"),
            "normalization_status": data.get("normalization_status"),
            "rows": rows,
            "exchanges_with_matches": matched_exchanges,
            "candidate_hints": coverage.get("direct_adapter_candidate_hints") or [],
            "by_exchange_statuses": {
                exchange: row.get("status")
                for exchange, row in by_exchange.items()
                if isinstance(row, dict)
            },
            "by_exchange_route_input_statuses": {
                exchange: row.get("route_input_status")
                for exchange, row in by_exchange.items()
                if isinstance(row, dict)
            },
            "read_only": data.get("read_only"),
            "execution_enabled": data.get("execution_enabled"),
            "ranking_enabled": data.get("ranking_enabled"),
            "production_signal_enabled": data.get("production_signal_enabled"),
        }
        endpoints["coinglass_perp_dex"] = {
            "http_status": status_code,
            "success": bool_payload_success(payload),
            "detail": payload.get("detail"),
        }
        if status_code != 200 or not bool_payload_success(payload):
            failures.append("coinglass: request_failed")
        if matched_exchanges < min_matched_exchanges:
            failures.append(f"coinglass: matched exchanges below threshold: {matched_exchanges} < {min_matched_exchanges}")
        if data.get("read_only") is not True:
            failures.append("coinglass: read_only_not_true")
        if data.get("execution_enabled") is not False:
            failures.append("coinglass: execution_enabled_true")
        if data.get("ranking_enabled") is True:
            failures.append("coinglass: ranking_enabled_true")
        if data.get("production_signal_enabled") is True:
            failures.append("coinglass: production_signal_enabled_true")

    policy_status, policy_payload = fetch_json("/api/v1/perp-dex/route-constraints", root_url)
    model_status, model_payload = fetch_json("/api/v1/perp-dex/route-model", root_url)
    policy_payload = as_dict(policy_payload)
    model_payload = as_dict(model_payload)
    policy = as_dict(policy_payload.get("data"))
    model = as_dict(model_payload.get("data"))
    policy_ui = as_dict(policy.get("ui_policy"))
    route_model_flags = route_model_output_flags(model)
    endpoints["route_constraints"] = {
        "http_status": policy_status,
        "success": bool_payload_success(policy_payload),
        "detail": policy_payload.get("detail"),
    }
    endpoints["route_model"] = {
        "http_status": model_status,
        "success": bool_payload_success(model_payload),
        "detail": model_payload.get("detail"),
    }

    if policy_status != 200 or not bool_payload_success(policy_payload):
        failures.append("route_policy: request_failed")
    if model_status != 200 or not bool_payload_success(model_payload):
        failures.append("route_model: request_failed")
    if policy.get("read_only") is not True:
        failures.append("route_policy: read_only_not_true")
    if policy.get("execution_enabled") is not False:
        failures.append("route_policy: execution_enabled_true")
    if policy.get("production_liquidity_signal") is True:
        failures.append("route_policy: production_liquidity_signal_true")
    if policy_ui.get("may_rank_by_liquidity") is True:
        failures.append("route_policy: may_rank_by_liquidity_true")
    if policy_ui.get("may_submit_orders") is True:
        failures.append("route_policy: may_submit_orders_true")
    if model.get("read_only") is not True:
        failures.append("route_model: read_only_not_true")
    if route_model_flags["execution_enabled"] is not False:
        failures.append("route_model: execution_enabled_true")
    if route_model_flags["ranking_enabled"] is True:
        failures.append("route_model: ranking_enabled_true")
    if route_model_flags["production_signal_enabled"] is True:
        failures.append("route_model: production_signal_enabled_true")
    if route_model_flags["may_estimate_cost_bps"] is True:
        failures.append("route_model: may_estimate_cost_bps_true")
    if route_model_flags["may_rank_routes"] is True:
        failures.append("route_model: may_rank_routes_true")
    if route_model_flags["may_submit_orders"] is True:
        failures.append("route_model: may_submit_orders_true")
    if route_model_flags["may_emit_numeric_total_bps"] is True:
        failures.append("route_model: may_emit_numeric_total_bps_true")

    direct_aggregate_status = "live" if normalized_live_venue_ids else "unavailable"
    coinglass_status = (
        "research_enrichment"
        if run_coinglass and coinglass["rows"] > 0
        else coinglass["status"]
    )
    row_ids = ["direct_venues", *venues]
    if run_coinglass:
        row_ids.append("coinglass_perpdex")
    row_ids.extend(["route_policy", "route_model", "release_smoke"])

    contract = {
        "source_status_contract_version": "source_status_v0",
        "source_status_row_ids": row_ids,
        "source_status_statuses": {
            "direct_venues": direct_aggregate_status,
            **{venue: direct_venues[venue]["snapshot_status"] for venue in venues},
            **({"coinglass_perpdex": coinglass_status} if run_coinglass else {}),
            "route_policy": policy.get("status"),
            "route_model": model.get("status"),
            "release_smoke": "passed",
        },
        "source_status_boundaries": {
            "direct_venues": "read_only_market_context_no_venue_ranking",
            **{
                venue: (
                    "gmx_diagnostics_only_no_liquidity_ranking"
                    if venue == "gmx"
                    else "display_only_venue_rows_no_execution_path"
                )
                for venue in venues
            },
            **({"coinglass_perpdex": "screening_hints_only_not_route_input"} if run_coinglass else {}),
            "route_policy": "ranking_and_execution_blocked",
            "route_model": "numeric_total_bps_blocked",
            "release_smoke": "read_only_safety_gates_confirmed",
        },
        "direct_venue_ids": venues,
        "direct_normalized_venue_ids": normalized_venue_ids,
        "direct_normalized_live_venue_ids": normalized_live_venue_ids,
        "direct_total_rows": total_direct_rows,
        "direct_rows_by_venue": {venue: direct_venues[venue]["rows"] for venue in venues},
        "direct_availability_statuses": {
            venue: direct_venues[venue]["availability_status"] for venue in venues
        },
        "direct_provider_error_classes": direct_provider_error_classes,
        "direct_depth_venue_ids": depth_venue_ids,
        "direct_depth_statuses": {
            venue: direct_venues[venue]["depth_statuses"] for venue in venues
        },
        "direct_depth_freshness_statuses": {
            venue: direct_venues[venue]["depth_freshness_status"]
            for venue in venues
            if direct_venues[venue]["depth_freshness_status"]
        },
        "direct_execution_enabled_venues": [
            venue for venue in venues if direct_venues[venue]["execution_enabled"] is True
        ],
        "direct_ranking_enabled_venues": [
            venue for venue in venues if direct_venues[venue]["ranking_enabled"] is True
        ],
        "direct_production_signal_enabled_venues": [
            venue for venue in venues if direct_venues[venue]["production_signal_enabled"] is True
        ],
        "coinglass_status": coinglass["status"],
        "coinglass_rows": coinglass["rows"],
        "coinglass_exchanges_with_matches": coinglass["exchanges_with_matches"],
        "coinglass_candidate_hints": coinglass["candidate_hints"],
        "coinglass_exchange_statuses": coinglass["by_exchange_statuses"],
        "coinglass_exchange_route_input_statuses": coinglass["by_exchange_route_input_statuses"],
        "coinglass_execution_enabled": coinglass["execution_enabled"],
        "coinglass_ranking_enabled": coinglass["ranking_enabled"],
        "coinglass_production_signal_enabled": coinglass["production_signal_enabled"],
        "route_policy_status": policy.get("status"),
        "route_policy_blocker_ids": [
            blocker.get("id") for blocker in as_list(policy.get("blockers")) if isinstance(blocker, dict)
        ],
        "route_policy_flags": {
            "read_only": policy.get("read_only"),
            "execution_enabled": policy.get("execution_enabled"),
            "production_liquidity_signal": policy.get("production_liquidity_signal"),
            "may_rank_by_liquidity": policy_ui.get("may_rank_by_liquidity"),
            "may_submit_orders": policy_ui.get("may_submit_orders"),
        },
        "route_model_status": model.get("status"),
        "route_model_required_input_ids": [
            item.get("id") for item in as_list(model.get("required_inputs")) if isinstance(item, dict)
        ],
        "route_model_blocker_ids": [
            blocker.get("id") for blocker in as_list(model.get("blockers")) if isinstance(blocker, dict)
        ],
        "route_model_flags": route_model_flags,
        "release_smoke_check_ids": [
            "server_smoke",
            "perp_dex_policy_smoke",
            "perp_dex_direct_smoke",
            "coinglass_perp_dex_coverage_smoke",
        ],
        "safe_boundary": "source status compare only; do not rank venues, estimate route cost or submit orders",
    }

    if total_direct_rows < min_total_rows:
        failures.append(f"direct venues total rows below threshold: {total_direct_rows} < {min_total_rows}")

    return {
        "base_url": root_url,
        "requested_symbols": symbols,
        "requested_venues": venues,
        "requested_exchanges": exchanges,
        "endpoints": endpoints,
        "contract": contract,
        "failures": failures,
    }


summary = compact_source_status(base_url)
failures = list(summary.pop("failures"))

if compare_base_url:
    compare_summary = compact_source_status(compare_base_url)
    compare_failures = compare_summary.pop("failures")
    diffs = diff_contracts(summary["contract"], compare_summary["contract"])
    summary["compare"] = {
        "base_url": compare_base_url,
        "contract": compare_summary["contract"],
        "diffs": diffs,
        "failures": compare_failures,
    }
    if compare_failures and not allow_unavailable:
        failures.extend(f"compare: {failure}" for failure in compare_failures)
    if diffs and fail_on_diff:
        failures.append("compare: source_status_contract_diff_detected")

print("ok")
print(json.dumps(summary, ensure_ascii=False, indent=2))

if failures and not allow_unavailable:
    raise SystemExit("; ".join(failures))
PY

printf 'Perp DEX source status smoke passed.\n'
