#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3001}"
FRONTEND_SMOKE_PATH="${FRONTEND_SMOKE_PATH:-/market}"

check() {
  name="$1"
  url="$2"
  printf '%s ... ' "$name"
  code="$(curl -fsS -o /tmp/deltagrid-smoke-response.txt -w '%{http_code}' "$url")"
  if [ "$code" != "200" ]; then
    printf 'FAILED (%s)\n' "$code"
    cat /tmp/deltagrid-smoke-response.txt
    exit 1
  fi
  printf 'ok\n'
}

check "backend health" "$BASE_URL/api/v1/health"
check "backend readiness" "$BASE_URL/api/v1/health/readiness"
check "data health" "$BASE_URL/api/v1/data/health"
check "frontend" "${FRONTEND_URL%/}$FRONTEND_SMOKE_PATH"

printf 'DeltaGrid smoke checks passed.\n'
