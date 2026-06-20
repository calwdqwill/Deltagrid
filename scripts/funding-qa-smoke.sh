#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3001}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
EXCHANGES="${EXCHANGES:-okx,coinglass}"
MIN_TOTAL_ROWS="${MIN_TOTAL_ROWS:-1}"
RUN_FRONTEND_CHECK="${RUN_FRONTEND_CHECK:-1}"
ALLOW_UNAVAILABLE="${ALLOW_UNAVAILABLE:-0}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMPARE_BASE_URL="${COMPARE_BASE_URL:-}"
FAIL_ON_DIFF="${FAIL_ON_DIFF:-0}"
FAIL_ON_RELEASE_NOT_READY="${FAIL_ON_RELEASE_NOT_READY:-0}"
OUTPUT_JSON_ONLY="${OUTPUT_JSON_ONLY:-0}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding QA smoke.\n' >&2
    exit 1
  fi
fi

if [ "$OUTPUT_JSON_ONLY" != "1" ]; then
  printf 'Funding QA smoke ... '
fi

"$PYTHON_BIN" - "$BASE_URL" "$FRONTEND_URL" "$SYMBOLS" "$EXCHANGES" "$MIN_TOTAL_ROWS" "$RUN_FRONTEND_CHECK" "$ALLOW_UNAVAILABLE" "$TIMEOUT_SECONDS" "$COMPARE_BASE_URL" "$FAIL_ON_DIFF" "$FAIL_ON_RELEASE_NOT_READY" "$OUTPUT_JSON_ONLY" <<'PY'
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

(
    base_url,
    frontend_url,
    symbols_raw,
    exchanges_raw,
    min_total_rows_raw,
    run_frontend_raw,
    allow_raw,
    timeout_raw,
    compare_base_url,
    fail_on_diff_raw,
    fail_on_release_not_ready_raw,
    output_json_only_raw,
) = sys.argv[1:13]

base_url = base_url.rstrip("/")
frontend_url = frontend_url.rstrip("/")
compare_base_url = compare_base_url.rstrip("/") if compare_base_url else ""
symbols = [item.strip().upper() for item in symbols_raw.split(",") if item.strip()]
exchanges = [item.strip().lower() for item in exchanges_raw.split(",") if item.strip()]
min_total_rows = int(min_total_rows_raw)
run_frontend_check = run_frontend_raw == "1"
allow_unavailable = allow_raw == "1"
timeout = int(timeout_raw)
fail_on_diff = fail_on_diff_raw == "1"
fail_on_release_not_ready = fail_on_release_not_ready_raw == "1"
output_json_only = output_json_only_raw == "1"

COMPARE_IGNORED_FIELDS = {
    "frontend_checked",
    "frontend_http_status",
    "frontend_markers",
    "latest_by_symbol_exchange",
    "latest_rate_presence",
}

if not symbols:
    raise SystemExit("SYMBOLS must contain at least one symbol")
if not exchanges:
    raise SystemExit("EXCHANGES must contain at least one exchange")


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


def fetch_text(path, root_url):
    request = Request(
        f"{root_url}{path}",
        headers={"Accept": "text/html", "User-Agent": "DeltaGridSmoke/1.0"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (URLError, TimeoutError) as exc:
        return None, str(exc)


def as_dict(value):
    return value if isinstance(value, dict) else {}


def as_list(value):
    return value if isinstance(value, list) else []


def bool_payload_success(payload):
    return bool(payload.get("success")) if isinstance(payload, dict) else False


def funding_rate(row):
    value = row.get("funding_rate") if isinstance(row, dict) else None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_row(rows):
    valid_rows = [
        row for row in rows
        if isinstance(row, dict) and isinstance(row.get("timestamp"), (int, float))
    ]
    if not valid_rows:
        return None
    return max(valid_rows, key=lambda row: row["timestamp"])


def health_stream_rows(health, section, exchange):
    report = as_dict(health.get(section))
    if section == "freshness":
        rows = as_list(report.get("streams"))
    else:
        rows = as_list(report.get("rows"))
    return [
        row for row in rows
        if isinstance(row, dict)
        and row.get("stream") == "funding_rates"
        and str(row.get("exchange", "")).lower() == exchange
    ]


def status_counts(rows):
    counts = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def source_pair_status(okx_rate, coinglass_rate):
    if okx_rate is None and coinglass_rate is None:
        return "no_source_pair"
    if okx_rate is None:
        return "missing_okx_side"
    if coinglass_rate is None:
        return "missing_coinglass_side"
    difference = abs(okx_rate - coinglass_rate) * 100
    if difference <= 0.005:
        return "aligned_sources"
    if difference <= 0.02:
        return "elevated_source_difference"
    return "divergent_source_difference"


def release_check(status, evidence, next_action):
    return {
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def funding_release_readiness(
    health_success,
    total_rows,
    funding_rows_by_source,
    frontend_markers,
    frontend_checked,
    safety_flags,
):
    missing_frontend_markers = [
        marker for marker, present in sorted(frontend_markers.items())
        if not present
    ]
    sources_with_rows = [
        exchange for exchange, rows in sorted(funding_rows_by_source.items())
        if rows > 0
    ]
    safety_locked = (
        safety_flags.get("read_only_analytics") is True
        and safety_flags.get("uses_existing_data_endpoints") is True
        and safety_flags.get("new_provider_calls_required") is False
        and safety_flags.get("trading_enabled") is False
        and safety_flags.get("execution_enabled") is False
        and safety_flags.get("route_ranking_enabled") is False
        and safety_flags.get("route_selection_enabled") is False
        and safety_flags.get("numeric_route_cost_bps_enabled") is False
        and safety_flags.get("diagnostic_carry_bps_enabled") is False
    )

    if not health_success:
        overall_status = "blocked_missing_health"
        next_action = "Fix /data/health before release smoke"
    elif total_rows <= 0:
        overall_status = "needs_funding_rows"
        next_action = "Run funding sync before preview/prod release smoke"
    elif frontend_checked and missing_frontend_markers:
        overall_status = "blocked_missing_frontend_markers"
        next_action = "Inspect Funding UI markers before release"
    elif not safety_locked:
        overall_status = "blocked_safety_flags"
        next_action = "Restore read-only safety flags before release"
    elif not frontend_checked:
        overall_status = "backend_ready_needs_frontend_check"
        next_action = "Run smoke with FRONTEND_URL for UI marker coverage"
    else:
        overall_status = "ready_for_preview_smoke"
        next_action = "Run preview/prod compare with FAIL_ON_DIFF=1"

    return {
        "status": overall_status,
        "next_action": next_action,
        "checks": {
            "data_health": release_check(
                "ready" if health_success else "missing",
                "data_health endpoint returned success" if health_success else "data_health endpoint failed",
                "Keep /data/health in release smoke" if health_success else "Fix backend health endpoint",
            ),
            "funding_rows": release_check(
                "loaded" if total_rows > 0 else "empty",
                f"{total_rows} funding rows across configured sources",
                "Keep MIN_TOTAL_ROWS guard enabled" if total_rows > 0 else "Run funding sync before release",
            ),
            "source_coverage": release_check(
                "both_sources_loaded" if len(sources_with_rows) == len(funding_rows_by_source) else "partial_source_coverage",
                ", ".join(f"{exchange}:{rows}" for exchange, rows in sorted(funding_rows_by_source.items())),
                "Compare source QA before rollout" if len(sources_with_rows) == len(funding_rows_by_source) else "Inspect missing source rows",
            ),
            "frontend_markers": release_check(
                "not_checked" if not frontend_checked else ("ready" if not missing_frontend_markers else "missing_markers"),
                "frontend marker check skipped" if not frontend_checked else f"{len(missing_frontend_markers)} missing markers",
                "Run with FRONTEND_URL" if not frontend_checked else ("Keep frontend marker check enabled" if not missing_frontend_markers else "Inspect Funding UI"),
            ),
            "compare_support": release_check(
                "ready",
                "COMPARE_BASE_URL emits compare.summary for drift checks",
                "Use FAIL_ON_DIFF=1 for release hard gate",
            ),
            "safety_boundary": release_check(
                "locked" if safety_locked else "unsafe",
                "read-only safety flags are locked" if safety_locked else "one or more forbidden outputs are enabled",
                "Do not enable forbidden outputs without product decision" if safety_locked else "Restore safety flags before release",
            ),
        },
        "missing_frontend_markers": missing_frontend_markers,
        "sources_with_rows": sources_with_rows,
    }


def compact_contract(root_url, frontend_root_url=None):
    failures = []
    endpoints = {}
    funding_rows_by_source = {}
    latest_by_symbol_exchange = {}
    latest_rates_by_symbol_exchange = {}

    status_code, health_payload = fetch_json("/api/v1/data/health", root_url)
    health_payload = as_dict(health_payload)
    health = as_dict(health_payload.get("data"))
    endpoints["data_health"] = {
        "http_status": status_code,
        "success": bool_payload_success(health_payload),
        "detail": health_payload.get("detail"),
    }
    if status_code != 200 or not bool_payload_success(health_payload):
        failures.append("data_health: request_failed")

    for exchange in exchanges:
        funding_rows_by_source[exchange] = 0
        for symbol in symbols:
            query = urlencode({"symbol": symbol, "exchange": exchange})
            endpoint_id = f"funding_{symbol.lower()}_{exchange}"
            status_code, payload = fetch_json(f"/api/v1/data/funding?{query}", root_url)
            payload = as_dict(payload)
            rows = as_list(payload.get("data"))
            latest = latest_row(rows)
            latest_rate = funding_rate(latest) if latest else None
            funding_rows_by_source[exchange] += len(rows)
            latest_by_symbol_exchange[f"{symbol}:{exchange}"] = latest.get("timestamp") if latest else None
            latest_rates_by_symbol_exchange[f"{symbol}:{exchange}"] = latest_rate
            endpoints[endpoint_id] = {
                "http_status": status_code,
                "success": bool_payload_success(payload),
                "rows": len(rows),
                "meta_count": as_dict(payload.get("meta")).get("count"),
                "detail": payload.get("detail"),
            }
            if status_code != 200 or not bool_payload_success(payload):
                failures.append(f"{endpoint_id}: request_failed")

    total_rows = sum(funding_rows_by_source.values())
    freshness_statuses = {
        exchange: status_counts(health_stream_rows(health, "freshness", exchange))
        for exchange in exchanges
    }
    coverage_statuses = {
        exchange: status_counts(health_stream_rows(health, "coverage", exchange))
        for exchange in exchanges
    }
    sync_health = as_dict(health.get("sync_health_by_type"))
    sync_statuses = {
        exchange: as_dict(as_dict(sync_health.get(exchange)).get("snapshots" if exchange == "coinglass" else "funding_rates")).get("status")
        for exchange in exchanges
    }
    source_pair_statuses = {
        symbol: source_pair_status(
            latest_rates_by_symbol_exchange.get(f"{symbol}:okx"),
            latest_rates_by_symbol_exchange.get(f"{symbol}:coinglass"),
        )
        for symbol in symbols
    }

    frontend_markers = {}
    frontend_status_code = None
    if run_frontend_check and frontend_root_url:
        frontend_status_code, html = fetch_text("/funding", frontend_root_url)
        qa_status_code, qa_html = fetch_text("/funding?view=qa", frontend_root_url)
        combined_html = f"{html}\n{qa_html}"
        frontend_markers = {
            "funding_qa_view": "Funding QA" in qa_html,
            "funding_release_checklist": "Funding Release Checklist" in combined_html,
            "funding_history_diagnostics": "Funding History Diagnostics" in combined_html,
            "funding_history_controls": "Funding History Controls" in combined_html,
            "funding_history_readiness": "Funding History Readiness" in combined_html,
            "funding_source_status": "Funding Source Status" in combined_html,
            "funding_freshness_anomaly": "Funding Freshness" in combined_html and "Anomaly" in combined_html,
            "funding_anomaly_detail": "Funding Anomaly Detail" in combined_html,
            "funding_source_comparison": "Funding Source Comparison" in combined_html,
            "funding_qa_drilldown": "Funding QA Drilldown" in combined_html,
            "read_only_boundary": "not a ranking signal" in combined_html or "not a trading or routing signal" in combined_html,
        }
        endpoints["frontend_funding"] = {
            "http_status": frontend_status_code,
            "success": frontend_status_code == 200,
            "markers": frontend_markers,
        }
        endpoints["frontend_funding_qa"] = {
            "http_status": qa_status_code,
            "success": qa_status_code == 200,
        }
        if frontend_status_code != 200:
            failures.append("frontend_funding: request_failed")
        if qa_status_code != 200:
            failures.append("frontend_funding_qa: request_failed")
        for marker, present in frontend_markers.items():
            if not present:
                failures.append(f"frontend_funding: missing_marker:{marker}")

    safety_flags = {
        "read_only_analytics": True,
        "uses_existing_data_endpoints": True,
        "new_provider_calls_required": False,
        "trading_enabled": False,
        "execution_enabled": False,
        "route_ranking_enabled": False,
        "route_selection_enabled": False,
        "numeric_route_cost_bps_enabled": False,
        "diagnostic_carry_bps_enabled": False,
        "full_payload_printed": False,
    }

    contract = {
        "funding_qa_contract_version": "funding_qa_v0",
        "panel_ids": [
            "funding_release_checklist",
            "funding_source_status",
            "funding_freshness_anomaly",
            "funding_anomaly_detail",
            "funding_history_diagnostics",
            "funding_history_controls",
            "funding_history_readiness",
            "funding_source_comparison",
            "funding_qa_drilldown",
        ],
        "symbols": symbols,
        "exchanges": exchanges,
        "funding_rows_by_source": funding_rows_by_source,
        "funding_total_rows": total_rows,
        "latest_by_symbol_exchange": latest_by_symbol_exchange,
        "latest_rate_presence": {
            key: value is not None
            for key, value in latest_rates_by_symbol_exchange.items()
        },
        "freshness_statuses": freshness_statuses,
        "coverage_statuses": coverage_statuses,
        "sync_statuses": sync_statuses,
        "source_pair_statuses": source_pair_statuses,
        "frontend_markers": frontend_markers,
        "frontend_checked": run_frontend_check and bool(frontend_root_url),
        "frontend_http_status": frontend_status_code,
        "release_readiness": funding_release_readiness(
            bool_payload_success(health_payload),
            total_rows,
            funding_rows_by_source,
            frontend_markers,
            run_frontend_check and bool(frontend_root_url),
            safety_flags,
        ),
        "safety_flags": safety_flags,
        "safe_boundary": "funding QA only; do not use as trading, carry, routing, ranking or execution signal",
    }

    if total_rows < min_total_rows:
        failures.append(f"funding total rows below threshold: {total_rows} < {min_total_rows}")

    return {
        "base_url": root_url,
        "frontend_url": frontend_root_url,
        "endpoints": endpoints,
        "contract": contract,
        "failures": failures,
    }


def diff_contracts(base_contract, compare_contract):
    diffs = []
    for field in sorted(set(base_contract) | set(compare_contract)):
        if field in COMPARE_IGNORED_FIELDS:
            continue
        base_value = base_contract.get(field)
        compare_value = compare_contract.get(field)
        if base_value != compare_value:
            diffs.append({"field": field, "base": base_value, "compare": compare_value})
    return diffs


def compare_status(diffs, compare_failures):
    if compare_failures:
        return "compare_failures"
    if diffs:
        return "diff_detected"
    return "aligned"


def compare_report(base_contract, compare_contract, diffs, compare_failures):
    return {
        "status": compare_status(diffs, compare_failures),
        "diff_count": len(diffs),
        "diff_fields": [diff["field"] for diff in diffs],
        "ignored_fields": sorted(COMPARE_IGNORED_FIELDS),
        "fail_on_diff": fail_on_diff,
        "fail_on_release_not_ready": fail_on_release_not_ready,
        "base_total_rows": base_contract.get("funding_total_rows"),
        "compare_total_rows": compare_contract.get("funding_total_rows"),
        "base_panel_ids": base_contract.get("panel_ids"),
        "compare_panel_ids": compare_contract.get("panel_ids"),
        "safety_flags_aligned": base_contract.get("safety_flags") == compare_contract.get("safety_flags"),
    }


summary = compact_contract(base_url, frontend_url if run_frontend_check else None)
failures = list(summary.pop("failures"))
release_status = as_dict(summary["contract"].get("release_readiness")).get("status")
if fail_on_release_not_ready and release_status != "ready_for_preview_smoke":
    failures.append(f"release_readiness: {release_status}")

if compare_base_url:
    compare_result = compact_contract(compare_base_url, None)
    compare_failures = compare_result.pop("failures")
    diffs = diff_contracts(summary["contract"], compare_result["contract"])
    summary["compare"] = {
        "base_url": base_url,
        "compare_base_url": compare_base_url,
        "summary": compare_report(summary["contract"], compare_result["contract"], diffs, compare_failures),
        "diffs": diffs,
        "failures": compare_failures,
        "contract": compare_result["contract"],
    }
    if compare_failures and not allow_unavailable:
        failures.extend(f"compare: {failure}" for failure in compare_failures)
    if diffs and fail_on_diff:
        failures.append("compare: funding_qa_contract_diff_detected")

if not output_json_only:
    print("ok")
print(json.dumps(summary, ensure_ascii=False, indent=2))

if failures and not allow_unavailable:
    raise SystemExit("; ".join(failures))
PY

if [ "$OUTPUT_JSON_ONLY" != "1" ]; then
  printf 'Funding QA smoke passed.\n'
fi
