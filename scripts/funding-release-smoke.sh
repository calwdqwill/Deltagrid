#!/usr/bin/env sh
set -eu

case "$0" in
  */*) SCRIPT_DIR=${0%/*} ;;
  *) SCRIPT_DIR=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR" && pwd)
QA_SMOKE_SCRIPT="$SCRIPT_DIR/funding-qa-smoke.sh"

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
FUNDING_RELEASE_STRICT="${FUNDING_RELEASE_STRICT:-${RELEASE_STRICT:-0}}"
OUTPUT_JSON_ONLY="${OUTPUT_JSON_ONLY:-0}"

case "$FUNDING_RELEASE_STRICT" in
  0|1) ;;
  *)
    printf 'FUNDING_RELEASE_STRICT must be 0 or 1.\n' >&2
    exit 1
    ;;
esac

case "$OUTPUT_JSON_ONLY" in
  0|1) ;;
  *)
    printf 'OUTPUT_JSON_ONLY must be 0 or 1.\n' >&2
    exit 1
    ;;
esac

if [ ! -f "$QA_SMOKE_SCRIPT" ]; then
  printf 'Missing Funding QA smoke script: %s\n' "$QA_SMOKE_SCRIPT" >&2
  exit 1
fi

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release smoke.\n' >&2
    exit 1
  fi
fi

if [ "$FUNDING_RELEASE_STRICT" = "1" ]; then
  FAIL_ON_DIFF="${FAIL_ON_DIFF:-1}"
  FAIL_ON_RELEASE_NOT_READY="${FAIL_ON_RELEASE_NOT_READY:-1}"
else
  FAIL_ON_DIFF="${FAIL_ON_DIFF:-0}"
  FAIL_ON_RELEASE_NOT_READY="${FAIL_ON_RELEASE_NOT_READY:-0}"
fi

export BASE_URL
export FRONTEND_URL
export SYMBOLS
export EXCHANGES
export MIN_TOTAL_ROWS
export RUN_FRONTEND_CHECK
export ALLOW_UNAVAILABLE
export TIMEOUT_SECONDS
export PYTHON_BIN
export COMPARE_BASE_URL
export FAIL_ON_DIFF
export FAIL_ON_RELEASE_NOT_READY
export OUTPUT_JSON_ONLY

if [ "$OUTPUT_JSON_ONLY" != "1" ]; then
  printf 'Funding release smoke ... base=%s frontend=%s compare=%s strict=%s frontend_check=%s min_rows=%s\n' \
    "$BASE_URL" \
    "$FRONTEND_URL" \
    "${COMPARE_BASE_URL:-none}" \
    "$FUNDING_RELEASE_STRICT" \
    "$RUN_FRONTEND_CHECK" \
    "$MIN_TOTAL_ROWS"
fi

. "$QA_SMOKE_SCRIPT"
