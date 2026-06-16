#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-http://127.0.0.1:8011}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:3012}"
CANDIDATE_SYMBOLS="${CANDIDATE_SYMBOLS:-HYPE,XRP,DOGE,ADA,LINK}"
MIN_CANDIDATE_OHLCV_ROWS="${MIN_CANDIDATE_OHLCV_ROWS:-1}"

TMP_DIR="${TMP_DIR:-/tmp}"
BODY_FILE="$TMP_DIR/deltagrid-preview-candidate-smoke-response.txt"

check_page_marker() {
  name="$1"
  url="$2"
  marker="$3"

  printf '%s ... ' "$name"
  code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' "$url")"
  if [ "$code" != "200" ]; then
    printf 'FAILED (%s)\n' "$code"
    cat "$BODY_FILE"
    exit 1
  fi
  if ! grep -q "$marker" "$BODY_FILE"; then
    printf 'FAILED (missing marker %s)\n' "$marker"
    exit 1
  fi
  printf 'ok\n'
}

check_window_rows() {
  symbol="$1"
  url="${BASE_URL%/}/api/v1/data/ohlcv/window?symbol=$symbol&exchange=okx&interval=1m&range=7d"

  printf 'candidate window %s ... ' "$symbol"
  code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' "$url")"
  if [ "$code" != "200" ]; then
    printf 'FAILED (%s)\n' "$code"
    cat "$BODY_FILE"
    exit 1
  fi

  rows="$(grep -o '"timestamp"' "$BODY_FILE" | wc -l | tr -d ' ')"
  if [ "$rows" -lt "$MIN_CANDIDATE_OHLCV_ROWS" ]; then
    printf 'FAILED (%s rows, expected at least %s)\n' "$rows" "$MIN_CANDIDATE_OHLCV_ROWS"
    exit 1
  fi
  printf 'ok (%s rows)\n' "$rows"
}

check_core_only_page() {
  path="$1"
  url="${FRONTEND_URL%/}$path"

  printf 'core-only page %s ... ' "$path"
  code="$(curl -sS -o "$BODY_FILE" -w '%{http_code}' "$url")"
  if [ "$code" != "200" ]; then
    printf 'FAILED (%s)\n' "$code"
    cat "$BODY_FILE"
    exit 1
  fi
  if grep -Eq 'HYPE|XRP|DOGE|ADA|LINK' "$BODY_FILE"; then
    printf 'FAILED (candidate marker leaked into core-only page)\n'
    exit 1
  fi
  printf 'ok\n'
}

for symbol in $(printf '%s' "$CANDIDATE_SYMBOLS" | tr ',' ' '); do
  check_page_marker "candidate chart $symbol" "${FRONTEND_URL%/}/charts?symbol=$symbol&interval=1m&range=7d" "$symbol"
  check_page_marker "candidate asset $symbol" "${FRONTEND_URL%/}/assets?symbol=$symbol" "$symbol"
  check_window_rows "$symbol"
done

check_core_only_page "/market-matrix"
check_core_only_page "/arbitrage-scanner"
check_core_only_page "/perp-dex"

printf 'DeltaGrid preview candidate smoke checks passed.\n'
