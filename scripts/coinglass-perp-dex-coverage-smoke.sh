#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
EXCHANGES="${EXCHANGES:-Aster,Lighter,EdgeX,Drift}"
MIN_ROWS="${MIN_ROWS:-1}"
MIN_MATCHED_EXCHANGES="${MIN_MATCHED_EXCHANGES:-1}"
ALLOW_UNAVAILABLE="${ALLOW_UNAVAILABLE:-0}"
TMP_DIR="${TMP_DIR:-/tmp}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for CoinGlass Perp DEX coverage smoke.\n' >&2
    exit 1
  fi
fi

mkdir -p "$TMP_DIR"
BODY_FILE="$TMP_DIR/deltagrid-coinglass-perp-dex-coverage-smoke.json"
CURL_ERROR_FILE="$TMP_DIR/deltagrid-coinglass-perp-dex-coverage-smoke.curl.err"

encoded_query="$("$PYTHON_BIN" - "$SYMBOLS" "$EXCHANGES" <<'PY'
import sys
from urllib.parse import urlencode

print(urlencode({"symbols": sys.argv[1], "exchanges": sys.argv[2]}))
PY
)"
url="${BASE_URL%/}/api/v1/perp-dex/venues/coinglass/markets?$encoded_query"

printf 'CoinGlass Perp DEX coverage smoke ... '
if ! code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' "$url" 2>"$CURL_ERROR_FILE")"; then
  printf 'FAILED (curl)\n'
  printf '{"error":"curl_failed","detail":'
  "$PYTHON_BIN" - "$CURL_ERROR_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    detail = handle.read().strip()
print(json.dumps(detail or "curl exited with non-zero status"))
PY
  printf '}\n'
  exit 1
fi
if [ "$code" != "200" ]; then
  printf 'FAILED (%s)\n' "$code"
  "$PYTHON_BIN" - "$BODY_FILE" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as handle:
        payload = json.load(handle)
except Exception as exc:
    print({"error": f"failed_to_parse_response: {exc}"})
    raise SystemExit(1)

print(json.dumps(
    {
        "success": payload.get("success"),
        "detail": payload.get("detail"),
        "meta": payload.get("meta"),
    },
    ensure_ascii=False,
    indent=2,
))
PY
  exit 1
fi

"$PYTHON_BIN" - "$BODY_FILE" "$MIN_ROWS" "$MIN_MATCHED_EXCHANGES" "$ALLOW_UNAVAILABLE" <<'PY'
import json
import sys

path, min_rows_raw, min_matched_raw, allow_unavailable_raw = sys.argv[1:5]
min_rows = int(min_rows_raw)
min_matched = int(min_matched_raw)
allow_unavailable = allow_unavailable_raw == "1"

with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

data = payload.get("data") or {}
coverage = data.get("coverage_summary") or {}
by_exchange = coverage.get("by_exchange") or {}
total_rows = int(coverage.get("total_rows") or 0)
matched_exchanges = int(coverage.get("exchanges_with_matches") or 0)
status = data.get("status")

compact = {
    "status": status,
    "requested_symbols": coverage.get("requested_symbols") or data.get("requested_symbols"),
    "requested_exchanges": coverage.get("requested_exchanges") or data.get("requested_exchanges"),
    "total_rows": total_rows,
    "exchanges_with_matches": matched_exchanges,
    "candidate_hints": coverage.get("direct_adapter_candidate_hints") or [],
    "field_totals": coverage.get("field_totals") or {},
    "by_exchange": {
        exchange: {
            "status": row.get("status"),
            "matched_rows": row.get("matched_rows"),
            "matched_symbols": row.get("matched_symbols"),
            "available_field_groups": row.get("available_field_groups"),
            "route_input_status": row.get("route_input_status"),
        }
        for exchange, row in by_exchange.items()
    },
}

print("ok")
print(json.dumps(compact, ensure_ascii=False, indent=2))

if status == "unavailable" and not allow_unavailable:
    raise SystemExit("CoinGlass Perp DEX endpoint is unavailable; check API key/provider response")
if total_rows < min_rows:
    raise SystemExit(f"CoinGlass Perp DEX rows below threshold: {total_rows} < {min_rows}")
if matched_exchanges < min_matched:
    raise SystemExit(
        f"CoinGlass Perp DEX matched exchanges below threshold: {matched_exchanges} < {min_matched}"
    )
PY

printf 'CoinGlass Perp DEX coverage smoke passed.\n'
