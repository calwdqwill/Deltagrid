#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
VENUES="${VENUES:-hyperliquid,dydx,lighter,aster,gmx}"
MIN_TOTAL_ROWS="${MIN_TOTAL_ROWS:-1}"
MIN_DEPTH_VENUES="${MIN_DEPTH_VENUES:-0}"
ALLOW_UNAVAILABLE="${ALLOW_UNAVAILABLE:-0}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-20}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Perp DEX direct smoke.\n' >&2
    exit 1
  fi
fi

printf 'Perp DEX direct venues smoke ... '
"$PYTHON_BIN" - "$BASE_URL" "$SYMBOLS" "$VENUES" "$MIN_TOTAL_ROWS" "$MIN_DEPTH_VENUES" "$ALLOW_UNAVAILABLE" "$TIMEOUT_SECONDS" <<'PY'
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

base_url, symbols, venues_raw, min_rows_raw, min_depth_raw, allow_raw, timeout_raw = sys.argv[1:8]
venues = [venue.strip().lower() for venue in venues_raw.split(",") if venue.strip()]
min_total_rows = int(min_rows_raw)
min_depth_venues = int(min_depth_raw)
allow_unavailable = allow_raw == "1"
timeout = int(timeout_raw)

if not venues:
    raise SystemExit("VENUES must contain at least one direct venue")

summary = {
    "base_url": base_url.rstrip("/"),
    "requested_symbols": [item.strip().upper() for item in symbols.split(",") if item.strip()],
    "requested_venues": venues,
    "total_rows": 0,
    "depth_venues": 0,
    "provider_error_classes": {},
    "execution_enabled_venues": [],
    "unsafe_signal_venues": [],
    "venues": {},
}
known_provider_error_classes = {
    "timeout",
    "rate_limit",
    "empty_response",
    "schema_drift",
    "unavailable_endpoint",
    "provider_unavailable",
    "provider_http_error",
}

failures = []

for venue in venues:
    query = urlencode({"symbols": symbols})
    url = f"{base_url.rstrip('/')}/api/v1/perp-dex/venues/{venue}/markets?{query}"
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "DeltaGridSmoke/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            status_code = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status_code = exc.code
        payload = {"success": False, "detail": str(exc)}
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        status_code = None
        payload = {"success": False, "detail": str(exc)}

    data = payload.get("data") if isinstance(payload, dict) else {}
    data = data if isinstance(data, dict) else {}
    detail = payload.get("detail") if isinstance(payload, dict) else {}
    detail = detail if isinstance(detail, dict) else {}
    markets = data.get("markets") if isinstance(data.get("markets"), list) else []
    availability = data.get("availability_summary") if isinstance(data.get("availability_summary"), dict) else {}
    if not availability and isinstance(detail.get("availability_summary"), dict):
        availability = detail["availability_summary"]
    provider_error_class = availability.get("provider_error_class") or detail.get("provider_error_class")
    depth_statuses = sorted(
        {
            str(row.get("orderbook_depth_status"))
            for row in markets
            if isinstance(row, dict) and row.get("orderbook_depth_status")
        }
    )
    read_only = data.get("read_only")
    execution_enabled = data.get("execution_enabled")
    ranking_enabled = data.get("ranking_enabled")
    production_signal_enabled = data.get("production_signal_enabled")
    rows = len(markets)
    summary["total_rows"] += rows
    if depth_statuses:
        summary["depth_venues"] += 1
    if execution_enabled is True:
        summary["execution_enabled_venues"].append(venue)
    if ranking_enabled is True or production_signal_enabled is True:
        summary["unsafe_signal_venues"].append(venue)
    if provider_error_class:
        summary["provider_error_classes"][provider_error_class] = (
            summary["provider_error_classes"].get(provider_error_class, 0) + 1
        )

    summary["venues"][venue] = {
        "http_status": status_code,
        "success": bool(payload.get("success")) if isinstance(payload, dict) else False,
        "snapshot_status": data.get("status"),
        "availability_status": availability.get("status"),
        "provider_error_class": provider_error_class,
        "rows": rows,
        "read_only": read_only,
        "execution_enabled": execution_enabled,
        "ranking_enabled": ranking_enabled,
        "production_signal_enabled": production_signal_enabled,
        "normalization_status": data.get("normalization_status"),
        "depth_statuses": depth_statuses,
        "availability_summary": {
            "rows": availability.get("rows"),
            "matched_symbols": availability.get("matched_symbols"),
            "missing_symbols": availability.get("missing_symbols"),
            "depth_diagnostics": availability.get("depth_diagnostics"),
            "depth_freshness": (availability.get("depth_diagnostics") or {}).get("freshness")
            if isinstance(availability.get("depth_diagnostics"), dict)
            else None,
            "safe_use": availability.get("safe_use"),
        } if availability else None,
        "markets": [
            {
                "symbol": row.get("symbol"),
                "market": row.get("market"),
                "status": row.get("status"),
                "depth_status": row.get("orderbook_depth_status"),
            }
            for row in markets
            if isinstance(row, dict)
        ],
    }

    if status_code != 200 or not payload.get("success"):
        failures.append(f"{venue}: request_failed")
    if not availability:
        failures.append(f"{venue}: missing_availability_summary")
    if provider_error_class and provider_error_class not in known_provider_error_classes:
        failures.append(f"{venue}: unknown_provider_error_class:{provider_error_class}")
    if availability:
        depth_diagnostics = availability.get("depth_diagnostics")
        depth_diagnostics = depth_diagnostics if isinstance(depth_diagnostics, dict) else {}
        freshness = depth_diagnostics.get("freshness")
        freshness = freshness if isinstance(freshness, dict) else {}
        if availability.get("read_only") is not True:
            failures.append(f"{venue}: availability_read_only_not_true")
        if availability.get("execution_enabled") is True:
            failures.append(f"{venue}: availability_execution_enabled_true")
        if availability.get("ranking_enabled") is True:
            failures.append(f"{venue}: availability_ranking_enabled_true")
        if availability.get("production_signal_enabled") is True:
            failures.append(f"{venue}: availability_production_signal_enabled_true")
        if not freshness:
            failures.append(f"{venue}: missing_depth_freshness_evidence")
        if freshness and freshness.get("may_emit_slippage_bps") is not False:
            failures.append(f"{venue}: depth_freshness_slippage_enabled")
        if freshness and freshness.get("numeric_total_status") != "blocked":
            failures.append(f"{venue}: depth_freshness_numeric_total_not_blocked")
    if read_only is not True:
        failures.append(f"{venue}: read_only_not_true")
    if execution_enabled is not False:
        failures.append(f"{venue}: execution_enabled_true")
    if ranking_enabled is True:
        failures.append(f"{venue}: ranking_enabled_true")
    if production_signal_enabled is True:
        failures.append(f"{venue}: production_signal_enabled_true")

print("ok")
print(json.dumps(summary, ensure_ascii=False, indent=2))

if summary["total_rows"] < min_total_rows:
    failures.append(f"total rows below threshold: {summary['total_rows']} < {min_total_rows}")
if summary["depth_venues"] < min_depth_venues:
    failures.append(f"depth venues below threshold: {summary['depth_venues']} < {min_depth_venues}")

if failures and not allow_unavailable:
    raise SystemExit("; ".join(failures))
PY

printf 'Perp DEX direct venues smoke passed.\n'
