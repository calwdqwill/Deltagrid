#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3001}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
RUN_COINGLASS="${RUN_COINGLASS:-1}"

export BASE_URL FRONTEND_URL SYMBOLS

cd "$(dirname "$0")/.."

run_step() {
  name="$1"
  shift
  printf '\n==> %s\n' "$name"
  "$@"
}

printf 'DeltaGrid release smoke started: base=%s frontend=%s symbols=%s\n' \
  "$BASE_URL" "$FRONTEND_URL" "$SYMBOLS"

run_step "server health/readiness/data/frontend smoke" \
  sh scripts/server-smoke.sh

run_step "Perp DEX route policy smoke" \
  sh scripts/perp-dex-policy-smoke.sh

run_step "Perp DEX direct venues smoke" \
  sh scripts/perp-dex-direct-smoke.sh

if [ "$RUN_COINGLASS" = "1" ]; then
  run_step "CoinGlass Perp DEX coverage smoke" \
    sh scripts/coinglass-perp-dex-coverage-smoke.sh
else
  printf '\n==> CoinGlass Perp DEX coverage smoke\n'
  printf 'skipped because RUN_COINGLASS=%s\n' "$RUN_COINGLASS"
fi

printf '\nDeltaGrid release smoke passed.\n'
