#!/usr/bin/env sh
set -eu

case "$0" in
  */*) SCRIPT_DIR=${0%/*} ;;
  *) SCRIPT_DIR=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR" && pwd)
REPORT_SCRIPT="$SCRIPT_DIR/funding-release-report.sh"
VALIDATE_SCRIPT="$SCRIPT_DIR/funding-release-report-validate.sh"
BUNDLE_VALIDATE_SCRIPT="$SCRIPT_DIR/funding-release-bundle-validate.sh"
BUNDLE_REVIEW_SCRIPT="$SCRIPT_DIR/funding-release-bundle-review.sh"
REVIEW_SUMMARY_SCRIPT="$SCRIPT_DIR/funding-release-review-summary.sh"
EVIDENCE_HANDOFF_SCRIPT="$SCRIPT_DIR/funding-release-evidence-handoff.sh"
EVIDENCE_AUDIT_SCRIPT="$SCRIPT_DIR/funding-release-evidence-audit.sh"
EVIDENCE_INDEX_SCRIPT="$SCRIPT_DIR/funding-release-evidence-index.sh"
EVIDENCE_VERIFY_SCRIPT="$SCRIPT_DIR/funding-release-evidence-verify.sh"
EVIDENCE_NOTES_SCRIPT="$SCRIPT_DIR/funding-release-evidence-notes.sh"
EVIDENCE_ARCHIVE_SCRIPT="$SCRIPT_DIR/funding-release-evidence-archive.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
FUNDING_RELEASE_CI_ARTIFACT_DIR="${FUNDING_RELEASE_CI_ARTIFACT_DIR:-artifacts/funding-release}"
FUNDING_RELEASE_CI_REPORT_FILE="${FUNDING_RELEASE_CI_REPORT_FILE:-funding-release-report.json}"
FUNDING_RELEASE_CI_VALIDATION_FILE="${FUNDING_RELEASE_CI_VALIDATION_FILE:-funding-release-validation.json}"
FUNDING_RELEASE_CI_MANIFEST_FILE="${FUNDING_RELEASE_CI_MANIFEST_FILE:-funding-release-manifest.json}"
FUNDING_RELEASE_CI_BUNDLE_VALIDATION_FILE="${FUNDING_RELEASE_CI_BUNDLE_VALIDATION_FILE:-funding-release-bundle-validation.json}"
FUNDING_RELEASE_CI_REVIEW_FILE="${FUNDING_RELEASE_CI_REVIEW_FILE:-funding-release-review.json}"
FUNDING_RELEASE_CI_SUMMARY_FILE="${FUNDING_RELEASE_CI_SUMMARY_FILE:-funding-release-summary.md}"
FUNDING_RELEASE_CI_HANDOFF_FILE="${FUNDING_RELEASE_CI_HANDOFF_FILE:-funding-release-handoff.md}"
FUNDING_RELEASE_CI_AUDIT_FILE="${FUNDING_RELEASE_CI_AUDIT_FILE:-funding-release-audit.json}"
FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE="${FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE:-funding-release-audit.md}"
FUNDING_RELEASE_CI_INDEX_FILE="${FUNDING_RELEASE_CI_INDEX_FILE:-funding-release-index.json}"
FUNDING_RELEASE_CI_INDEX_MARKDOWN_FILE="${FUNDING_RELEASE_CI_INDEX_MARKDOWN_FILE:-funding-release-index.md}"
FUNDING_RELEASE_CI_VERIFY_FILE="${FUNDING_RELEASE_CI_VERIFY_FILE:-funding-release-verify.json}"
FUNDING_RELEASE_CI_VERIFY_MARKDOWN_FILE="${FUNDING_RELEASE_CI_VERIFY_MARKDOWN_FILE:-funding-release-verify.md}"
FUNDING_RELEASE_CI_NOTES_FILE="${FUNDING_RELEASE_CI_NOTES_FILE:-funding-release-notes.json}"
FUNDING_RELEASE_CI_NOTES_MARKDOWN_FILE="${FUNDING_RELEASE_CI_NOTES_MARKDOWN_FILE:-funding-release-notes.md}"
FUNDING_RELEASE_CI_ARCHIVE_FILE="${FUNDING_RELEASE_CI_ARCHIVE_FILE:-funding-release-archive.json}"
FUNDING_RELEASE_CI_ARCHIVE_MARKDOWN_FILE="${FUNDING_RELEASE_CI_ARCHIVE_MARKDOWN_FILE:-funding-release-archive.md}"
FUNDING_RELEASE_CI_STATUS_FILE="${FUNDING_RELEASE_CI_STATUS_FILE:-funding-release-ci-status.json}"
FUNDING_RELEASE_CI_STDOUT_FILE="${FUNDING_RELEASE_CI_STDOUT_FILE:-}"
FUNDING_RELEASE_CI_VALIDATE_ONLY="${FUNDING_RELEASE_CI_VALIDATE_ONLY:-0}"
FUNDING_RELEASE_CI_VALIDATE_ARTIFACT="${FUNDING_RELEASE_CI_VALIDATE_ARTIFACT:-1}"
FUNDING_RELEASE_CI_WRITE_MANIFEST="${FUNDING_RELEASE_CI_WRITE_MANIFEST:-1}"
FUNDING_RELEASE_CI_VALIDATE_BUNDLE="${FUNDING_RELEASE_CI_VALIDATE_BUNDLE:-1}"
FUNDING_RELEASE_CI_WRITE_REVIEW="${FUNDING_RELEASE_CI_WRITE_REVIEW:-1}"
FUNDING_RELEASE_CI_WRITE_SUMMARY="${FUNDING_RELEASE_CI_WRITE_SUMMARY:-1}"
FUNDING_RELEASE_CI_WRITE_HANDOFF="${FUNDING_RELEASE_CI_WRITE_HANDOFF:-1}"
FUNDING_RELEASE_CI_WRITE_AUDIT="${FUNDING_RELEASE_CI_WRITE_AUDIT:-1}"
FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN="${FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN:-1}"
FUNDING_RELEASE_CI_WRITE_INDEX="${FUNDING_RELEASE_CI_WRITE_INDEX:-1}"
FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN="${FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN:-1}"
FUNDING_RELEASE_CI_WRITE_VERIFY="${FUNDING_RELEASE_CI_WRITE_VERIFY:-1}"
FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN="${FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN:-1}"
FUNDING_RELEASE_CI_WRITE_NOTES="${FUNDING_RELEASE_CI_WRITE_NOTES:-1}"
FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN="${FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN:-1}"
FUNDING_RELEASE_CI_WRITE_ARCHIVE="${FUNDING_RELEASE_CI_WRITE_ARCHIVE:-1}"
FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN="${FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN:-1}"
FUNDING_RELEASE_CI_WRITE_STATUS="${FUNDING_RELEASE_CI_WRITE_STATUS:-1}"

require_bool() {
  name="$1"
  value="$2"
  case "$value" in
    0|1) ;;
    *)
      printf '%s must be 0 or 1.\n' "$name" >&2
      exit 1
      ;;
  esac
}

path_parent_dir() {
  case "$1" in
    /*/*) printf '%s\n' "${1%/*}" ;;
    /*) printf '/\n' ;;
    */*) printf '%s\n' "${1%/*}" ;;
    *) printf '.\n' ;;
  esac
}

artifact_path() {
  candidate="$1"
  case "$candidate" in
    /*) printf '%s\n' "$candidate" ;;
    */*) printf '%s\n' "$candidate" ;;
    *) printf '%s/%s\n' "$FUNDING_RELEASE_CI_ARTIFACT_DIR" "$candidate" ;;
  esac
}

require_bool "FUNDING_RELEASE_CI_VALIDATE_ONLY" "$FUNDING_RELEASE_CI_VALIDATE_ONLY"
require_bool "FUNDING_RELEASE_CI_VALIDATE_ARTIFACT" "$FUNDING_RELEASE_CI_VALIDATE_ARTIFACT"
require_bool "FUNDING_RELEASE_CI_WRITE_MANIFEST" "$FUNDING_RELEASE_CI_WRITE_MANIFEST"
require_bool "FUNDING_RELEASE_CI_VALIDATE_BUNDLE" "$FUNDING_RELEASE_CI_VALIDATE_BUNDLE"
require_bool "FUNDING_RELEASE_CI_WRITE_REVIEW" "$FUNDING_RELEASE_CI_WRITE_REVIEW"
require_bool "FUNDING_RELEASE_CI_WRITE_SUMMARY" "$FUNDING_RELEASE_CI_WRITE_SUMMARY"
require_bool "FUNDING_RELEASE_CI_WRITE_HANDOFF" "$FUNDING_RELEASE_CI_WRITE_HANDOFF"
require_bool "FUNDING_RELEASE_CI_WRITE_AUDIT" "$FUNDING_RELEASE_CI_WRITE_AUDIT"
require_bool "FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN" "$FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN"
require_bool "FUNDING_RELEASE_CI_WRITE_INDEX" "$FUNDING_RELEASE_CI_WRITE_INDEX"
require_bool "FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN" "$FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN"
require_bool "FUNDING_RELEASE_CI_WRITE_VERIFY" "$FUNDING_RELEASE_CI_WRITE_VERIFY"
require_bool "FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN" "$FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN"
require_bool "FUNDING_RELEASE_CI_WRITE_NOTES" "$FUNDING_RELEASE_CI_WRITE_NOTES"
require_bool "FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN" "$FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN"
require_bool "FUNDING_RELEASE_CI_WRITE_ARCHIVE" "$FUNDING_RELEASE_CI_WRITE_ARCHIVE"
require_bool "FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN" "$FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN"
require_bool "FUNDING_RELEASE_CI_WRITE_STATUS" "$FUNDING_RELEASE_CI_WRITE_STATUS"
require_bool "RUN_FRONTEND_CHECK" "${RUN_FRONTEND_CHECK:-1}"
require_bool "KEEP_FUNDING_RELEASE_REPORT_JSON" "${KEEP_FUNDING_RELEASE_REPORT_JSON:-0}"

if [ ! -f "$REPORT_SCRIPT" ]; then
  printf 'Missing Funding release report script: %s\n' "$REPORT_SCRIPT" >&2
  exit 1
fi

if [ "$FUNDING_RELEASE_CI_VALIDATE_ARTIFACT" = "1" ] && [ ! -f "$VALIDATE_SCRIPT" ]; then
  printf 'Missing Funding release report validation script: %s\n' "$VALIDATE_SCRIPT" >&2
  exit 1
fi

if [ "$FUNDING_RELEASE_CI_VALIDATE_BUNDLE" = "1" ] && [ ! -f "$BUNDLE_VALIDATE_SCRIPT" ]; then
  printf 'Missing Funding release bundle validation script: %s\n' "$BUNDLE_VALIDATE_SCRIPT" >&2
  exit 1
fi

if [ "$FUNDING_RELEASE_CI_WRITE_REVIEW" = "1" ] && [ ! -f "$BUNDLE_REVIEW_SCRIPT" ]; then
  printf 'Missing Funding release bundle review script: %s\n' "$BUNDLE_REVIEW_SCRIPT" >&2
  exit 1
fi

if [ "$FUNDING_RELEASE_CI_WRITE_SUMMARY" = "1" ] && [ ! -f "$REVIEW_SUMMARY_SCRIPT" ]; then
  printf 'Missing Funding release review summary script: %s\n' "$REVIEW_SUMMARY_SCRIPT" >&2
  exit 1
fi

if [ "$FUNDING_RELEASE_CI_WRITE_HANDOFF" = "1" ] && [ ! -f "$EVIDENCE_HANDOFF_SCRIPT" ]; then
  printf 'Missing Funding release evidence handoff script: %s\n' "$EVIDENCE_HANDOFF_SCRIPT" >&2
  exit 1
fi

if { [ "$FUNDING_RELEASE_CI_WRITE_AUDIT" = "1" ] || [ "$FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN" = "1" ]; } && [ ! -f "$EVIDENCE_AUDIT_SCRIPT" ]; then
  printf 'Missing Funding release evidence audit script: %s\n' "$EVIDENCE_AUDIT_SCRIPT" >&2
  exit 1
fi

if { [ "$FUNDING_RELEASE_CI_WRITE_INDEX" = "1" ] || [ "$FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN" = "1" ]; } && [ ! -f "$EVIDENCE_INDEX_SCRIPT" ]; then
  printf 'Missing Funding release evidence index script: %s\n' "$EVIDENCE_INDEX_SCRIPT" >&2
  exit 1
fi

if { [ "$FUNDING_RELEASE_CI_WRITE_VERIFY" = "1" ] || [ "$FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN" = "1" ]; } && [ ! -f "$EVIDENCE_VERIFY_SCRIPT" ]; then
  printf 'Missing Funding release evidence verify script: %s\n' "$EVIDENCE_VERIFY_SCRIPT" >&2
  exit 1
fi

if { [ "$FUNDING_RELEASE_CI_WRITE_NOTES" = "1" ] || [ "$FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN" = "1" ]; } && [ ! -f "$EVIDENCE_NOTES_SCRIPT" ]; then
  printf 'Missing Funding release evidence notes script: %s\n' "$EVIDENCE_NOTES_SCRIPT" >&2
  exit 1
fi

if { [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE" = "1" ] || [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN" = "1" ]; } && [ ! -f "$EVIDENCE_ARCHIVE_SCRIPT" ]; then
  printf 'Missing Funding release evidence archive script: %s\n' "$EVIDENCE_ARCHIVE_SCRIPT" >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_ARTIFACT_DIR" ]; then
  printf 'FUNDING_RELEASE_CI_ARTIFACT_DIR must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_REPORT_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_REPORT_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_VALIDATION_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_VALIDATION_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_MANIFEST_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_MANIFEST_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_BUNDLE_VALIDATION_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_BUNDLE_VALIDATION_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_REVIEW_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_REVIEW_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_SUMMARY_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_SUMMARY_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_HANDOFF_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_HANDOFF_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_AUDIT_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_AUDIT_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_INDEX_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_INDEX_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_INDEX_MARKDOWN_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_INDEX_MARKDOWN_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_VERIFY_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_VERIFY_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_VERIFY_MARKDOWN_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_VERIFY_MARKDOWN_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_NOTES_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_NOTES_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_NOTES_MARKDOWN_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_NOTES_MARKDOWN_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_ARCHIVE_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_ARCHIVE_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_ARCHIVE_MARKDOWN_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_ARCHIVE_MARKDOWN_FILE must not be empty.\n' >&2
  exit 1
fi

if [ -z "$FUNDING_RELEASE_CI_STATUS_FILE" ]; then
  printf 'FUNDING_RELEASE_CI_STATUS_FILE must not be empty.\n' >&2
  exit 1
fi

mkdir -p "$FUNDING_RELEASE_CI_ARTIFACT_DIR"

REPORT_OUTPUT_FILE="${FUNDING_RELEASE_REPORT_OUTPUT:-$(artifact_path "$FUNDING_RELEASE_CI_REPORT_FILE")}"
VALIDATION_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_VALIDATION_FILE")"
MANIFEST_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_MANIFEST_FILE")"
BUNDLE_VALIDATION_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_BUNDLE_VALIDATION_FILE")"
REVIEW_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_REVIEW_FILE")"
SUMMARY_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_SUMMARY_FILE")"
HANDOFF_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_HANDOFF_FILE")"
AUDIT_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_AUDIT_FILE")"
AUDIT_MARKDOWN_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_AUDIT_MARKDOWN_FILE")"
INDEX_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_INDEX_FILE")"
INDEX_MARKDOWN_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_INDEX_MARKDOWN_FILE")"
VERIFY_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_VERIFY_FILE")"
VERIFY_MARKDOWN_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_VERIFY_MARKDOWN_FILE")"
NOTES_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_NOTES_FILE")"
NOTES_MARKDOWN_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_NOTES_MARKDOWN_FILE")"
ARCHIVE_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_ARCHIVE_FILE")"
ARCHIVE_MARKDOWN_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_ARCHIVE_MARKDOWN_FILE")"
STATUS_OUTPUT_FILE="$(artifact_path "$FUNDING_RELEASE_CI_STATUS_FILE")"
REPORT_OUTPUT_PARENT=$(path_parent_dir "$REPORT_OUTPUT_FILE")
if [ ! -d "$REPORT_OUTPUT_PARENT" ]; then
  mkdir -p "$REPORT_OUTPUT_PARENT"
fi

VALIDATION_OUTPUT_PARENT=$(path_parent_dir "$VALIDATION_OUTPUT_FILE")
if [ ! -d "$VALIDATION_OUTPUT_PARENT" ]; then
  mkdir -p "$VALIDATION_OUTPUT_PARENT"
fi

MANIFEST_OUTPUT_PARENT=$(path_parent_dir "$MANIFEST_OUTPUT_FILE")
if [ ! -d "$MANIFEST_OUTPUT_PARENT" ]; then
  mkdir -p "$MANIFEST_OUTPUT_PARENT"
fi

BUNDLE_VALIDATION_OUTPUT_PARENT=$(path_parent_dir "$BUNDLE_VALIDATION_OUTPUT_FILE")
if [ ! -d "$BUNDLE_VALIDATION_OUTPUT_PARENT" ]; then
  mkdir -p "$BUNDLE_VALIDATION_OUTPUT_PARENT"
fi

REVIEW_OUTPUT_PARENT=$(path_parent_dir "$REVIEW_OUTPUT_FILE")
if [ ! -d "$REVIEW_OUTPUT_PARENT" ]; then
  mkdir -p "$REVIEW_OUTPUT_PARENT"
fi

SUMMARY_OUTPUT_PARENT=$(path_parent_dir "$SUMMARY_OUTPUT_FILE")
if [ ! -d "$SUMMARY_OUTPUT_PARENT" ]; then
  mkdir -p "$SUMMARY_OUTPUT_PARENT"
fi

HANDOFF_OUTPUT_PARENT=$(path_parent_dir "$HANDOFF_OUTPUT_FILE")
if [ ! -d "$HANDOFF_OUTPUT_PARENT" ]; then
  mkdir -p "$HANDOFF_OUTPUT_PARENT"
fi

AUDIT_OUTPUT_PARENT=$(path_parent_dir "$AUDIT_OUTPUT_FILE")
if [ ! -d "$AUDIT_OUTPUT_PARENT" ]; then
  mkdir -p "$AUDIT_OUTPUT_PARENT"
fi

AUDIT_MARKDOWN_OUTPUT_PARENT=$(path_parent_dir "$AUDIT_MARKDOWN_OUTPUT_FILE")
if [ ! -d "$AUDIT_MARKDOWN_OUTPUT_PARENT" ]; then
  mkdir -p "$AUDIT_MARKDOWN_OUTPUT_PARENT"
fi

INDEX_OUTPUT_PARENT=$(path_parent_dir "$INDEX_OUTPUT_FILE")
if [ ! -d "$INDEX_OUTPUT_PARENT" ]; then
  mkdir -p "$INDEX_OUTPUT_PARENT"
fi

INDEX_MARKDOWN_OUTPUT_PARENT=$(path_parent_dir "$INDEX_MARKDOWN_OUTPUT_FILE")
if [ ! -d "$INDEX_MARKDOWN_OUTPUT_PARENT" ]; then
  mkdir -p "$INDEX_MARKDOWN_OUTPUT_PARENT"
fi

VERIFY_OUTPUT_PARENT=$(path_parent_dir "$VERIFY_OUTPUT_FILE")
if [ ! -d "$VERIFY_OUTPUT_PARENT" ]; then
  mkdir -p "$VERIFY_OUTPUT_PARENT"
fi

VERIFY_MARKDOWN_OUTPUT_PARENT=$(path_parent_dir "$VERIFY_MARKDOWN_OUTPUT_FILE")
if [ ! -d "$VERIFY_MARKDOWN_OUTPUT_PARENT" ]; then
  mkdir -p "$VERIFY_MARKDOWN_OUTPUT_PARENT"
fi

NOTES_OUTPUT_PARENT=$(path_parent_dir "$NOTES_OUTPUT_FILE")
if [ ! -d "$NOTES_OUTPUT_PARENT" ]; then
  mkdir -p "$NOTES_OUTPUT_PARENT"
fi

NOTES_MARKDOWN_OUTPUT_PARENT=$(path_parent_dir "$NOTES_MARKDOWN_OUTPUT_FILE")
if [ ! -d "$NOTES_MARKDOWN_OUTPUT_PARENT" ]; then
  mkdir -p "$NOTES_MARKDOWN_OUTPUT_PARENT"
fi

ARCHIVE_OUTPUT_PARENT=$(path_parent_dir "$ARCHIVE_OUTPUT_FILE")
if [ ! -d "$ARCHIVE_OUTPUT_PARENT" ]; then
  mkdir -p "$ARCHIVE_OUTPUT_PARENT"
fi

ARCHIVE_MARKDOWN_OUTPUT_PARENT=$(path_parent_dir "$ARCHIVE_MARKDOWN_OUTPUT_FILE")
if [ ! -d "$ARCHIVE_MARKDOWN_OUTPUT_PARENT" ]; then
  mkdir -p "$ARCHIVE_MARKDOWN_OUTPUT_PARENT"
fi

STATUS_OUTPUT_PARENT=$(path_parent_dir "$STATUS_OUTPUT_FILE")
if [ ! -d "$STATUS_OUTPUT_PARENT" ]; then
  mkdir -p "$STATUS_OUTPUT_PARENT"
fi

if [ -n "$FUNDING_RELEASE_CI_STDOUT_FILE" ]; then
  STDOUT_PARENT=$(path_parent_dir "$FUNDING_RELEASE_CI_STDOUT_FILE")
  if [ ! -d "$STDOUT_PARENT" ]; then
    mkdir -p "$STDOUT_PARENT"
  fi
fi

FUNDING_RELEASE_REPORT_PROFILE="${FUNDING_RELEASE_REPORT_PROFILE:-ci}"
FUNDING_RELEASE_REPORT_FORMAT="${FUNDING_RELEASE_REPORT_FORMAT:-json}"
FUNDING_RELEASE_REPORT_OUTPUT="$REPORT_OUTPUT_FILE"
RUN_FRONTEND_CHECK="${RUN_FRONTEND_CHECK:-1}"
MIN_TOTAL_ROWS="${MIN_TOTAL_ROWS:-1}"

export FUNDING_RELEASE_REPORT_PROFILE
export FUNDING_RELEASE_REPORT_FORMAT
export FUNDING_RELEASE_REPORT_OUTPUT
export RUN_FRONTEND_CHECK
export MIN_TOTAL_ROWS

printf 'Funding release CI report ... artifact=%s profile=%s format=%s base=%s compare=%s\n' \
  "$FUNDING_RELEASE_REPORT_OUTPUT" \
  "$FUNDING_RELEASE_REPORT_PROFILE" \
  "$FUNDING_RELEASE_REPORT_FORMAT" \
  "${BASE_URL:-http://127.0.0.1:8000}" \
  "${COMPARE_BASE_URL:-none}" >&2

if [ "$FUNDING_RELEASE_CI_VALIDATE_ONLY" = "1" ]; then
  printf 'Funding release CI report validation passed.\n' >&2
  exit 0
fi

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release CI report.\n' >&2
    exit 1
  fi
fi
export PYTHON_BIN

validate_report_artifact() {
  report_exit="$1"
  if [ "$FUNDING_RELEASE_CI_VALIDATE_ARTIFACT" != "1" ]; then
    return 0
  fi
  if [ ! -f "$FUNDING_RELEASE_REPORT_OUTPUT" ]; then
    if [ "$report_exit" = "0" ]; then
      printf 'Funding release report artifact missing after successful report: %s\n' "$FUNDING_RELEASE_REPORT_OUTPUT" >&2
      return 1
    fi
    printf 'Funding release report artifact unavailable after report exit %s; skipping artifact validation.\n' "$report_exit" >&2
    return 0
  fi
  set +e
  FUNDING_RELEASE_REPORT_VALIDATE_FILE="$FUNDING_RELEASE_REPORT_OUTPUT" \
    FUNDING_RELEASE_REPORT_VALIDATE_FORMAT=json \
    sh "$VALIDATE_SCRIPT" > "$VALIDATION_OUTPUT_FILE"
  validation_exit=$?
  set -e
  if [ "$validation_exit" -eq 0 ]; then
    printf 'Funding release report validation passed: %s\n' "$VALIDATION_OUTPUT_FILE" >&2
  else
    printf 'Funding release report validation failed: %s\n' "$VALIDATION_OUTPUT_FILE" >&2
    if [ -f "$VALIDATION_OUTPUT_FILE" ]; then
      cat "$VALIDATION_OUTPUT_FILE" >&2
    fi
  fi
  return "$validation_exit"
}

write_bundle_manifest() {
  report_exit="$1"
  validation_exit="$2"
  if [ "$FUNDING_RELEASE_CI_WRITE_MANIFEST" != "1" ]; then
    return 0
  fi
  "$PYTHON_BIN" - \
    "$MANIFEST_OUTPUT_FILE" \
    "$FUNDING_RELEASE_REPORT_OUTPUT" \
    "$FUNDING_RELEASE_CI_STDOUT_FILE" \
    "$VALIDATION_OUTPUT_FILE" \
    "$report_exit" \
    "$validation_exit" \
    "$FUNDING_RELEASE_CI_VALIDATE_ARTIFACT" \
    "$FUNDING_RELEASE_CI_WRITE_MANIFEST" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    manifest_path_raw,
    report_path_raw,
    stdout_path_raw,
    validation_path_raw,
    report_exit_raw,
    validation_exit_raw,
    validate_enabled_raw,
    write_manifest_raw,
) = sys.argv[1:9]

manifest_path = Path(manifest_path_raw)
report_path = Path(report_path_raw)
stdout_path = Path(stdout_path_raw) if stdout_path_raw else None
validation_path = Path(validation_path_raw)
report_exit = int(report_exit_raw)
validation_exit = int(validation_exit_raw)

def file_info(path):
    if path is None:
        return {"configured": False, "path": None, "exists": False}
    info = {"configured": True, "path": str(path), "exists": path.is_file()}
    if not path.is_file():
        return info
    data = path.read_bytes()
    info.update({
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
    try:
        json.loads(data.decode("utf-8"))
        info["json_valid"] = True
    except Exception:
        info["json_valid"] = False
    return info

def read_json(path):
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}

report = read_json(report_path)
validation = read_json(validation_path)
summary = report.get("release_gate_summary") if isinstance(report.get("release_gate_summary"), dict) else {}
run_context = report.get("run_context") if isinstance(report.get("run_context"), dict) else {}
bundle_exit_code = validation_exit if validation_exit != 0 else report_exit
blocking_ids = summary.get("blocking_ids") if isinstance(summary.get("blocking_ids"), list) else []
required_blocking_ids = (
    summary.get("required_blocking_ids")
    if isinstance(summary.get("required_blocking_ids"), list)
    else blocking_ids
)
optional_blocking_ids = (
    summary.get("optional_blocking_ids")
    if isinstance(summary.get("optional_blocking_ids"), list)
    else []
)
first_blocking_action = summary.get("first_blocking_action") if required_blocking_ids else None
first_optional_action = (
    summary.get("first_blocking_action")
    if not required_blocking_ids and optional_blocking_ids
    else None
)

manifest = {
    "manifest_version": "funding_release_ci_bundle_v0",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "bundle_exit_code": bundle_exit_code,
    "report_exit_code": report_exit,
    "validation_exit_code": validation_exit,
    "validation_enabled": validate_enabled_raw == "1",
    "manifest_enabled": write_manifest_raw == "1",
    "artifact_status": {
        "release_gate_status": report.get("release_gate_status"),
        "exit_reason": report.get("exit_reason"),
        "validation_status": validation.get("status") if validation else None,
        "validation_error_count": validation.get("error_count") if validation else None,
        "validation_warning_count": validation.get("warning_count") if validation else None,
    },
    "report_summary": {
        "report_version": report.get("report_version"),
        "contract": report.get("contract"),
        "readiness_gate_status": report.get("readiness_gate_status"),
        "readiness_status": report.get("readiness_status"),
        "compare_gate_status": report.get("compare_gate_status"),
        "compare_status": report.get("compare_status"),
        "blocking_ids": required_blocking_ids,
        "required_blocking_ids": required_blocking_ids,
        "optional_blocking_ids": optional_blocking_ids,
        "first_blocking_action": first_blocking_action,
        "first_optional_action": first_optional_action,
    },
    "run_context": run_context,
    "files": {
        "report": file_info(report_path),
        "stdout": file_info(stdout_path),
        "validation": file_info(validation_path),
        "manifest": {
            "configured": True,
            "path": str(manifest_path),
            "exists": False,
        },
    },
}

manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
  printf 'Funding release CI manifest written: %s\n' "$MANIFEST_OUTPUT_FILE" >&2
}

validate_bundle_manifest() {
  if [ "$FUNDING_RELEASE_CI_VALIDATE_BUNDLE" != "1" ]; then
    return 0
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_MANIFEST" != "1" ]; then
    printf 'Funding release bundle validation skipped because manifest writing is disabled.\n' >&2
    return 0
  fi
  if [ ! -f "$MANIFEST_OUTPUT_FILE" ]; then
    printf 'Funding release bundle manifest missing before validation: %s\n' "$MANIFEST_OUTPUT_FILE" >&2
    return 1
  fi
  set +e
  FUNDING_RELEASE_BUNDLE_VALIDATE_FILE="$MANIFEST_OUTPUT_FILE" \
    FUNDING_RELEASE_BUNDLE_VALIDATE_FORMAT=json \
    sh "$BUNDLE_VALIDATE_SCRIPT" > "$BUNDLE_VALIDATION_OUTPUT_FILE"
  bundle_validation_exit=$?
  set -e
  if [ "$bundle_validation_exit" -eq 0 ]; then
    printf 'Funding release bundle validation passed: %s\n' "$BUNDLE_VALIDATION_OUTPUT_FILE" >&2
  else
    printf 'Funding release bundle validation failed: %s\n' "$BUNDLE_VALIDATION_OUTPUT_FILE" >&2
    if [ -f "$BUNDLE_VALIDATION_OUTPUT_FILE" ]; then
      cat "$BUNDLE_VALIDATION_OUTPUT_FILE" >&2
    fi
  fi
  return "$bundle_validation_exit"
}

write_bundle_review() {
  if [ "$FUNDING_RELEASE_CI_WRITE_REVIEW" != "1" ]; then
    return 0
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_MANIFEST" != "1" ]; then
    printf 'Funding release bundle review skipped because manifest writing is disabled.\n' >&2
    return 0
  fi
  if [ ! -f "$MANIFEST_OUTPUT_FILE" ]; then
    printf 'Funding release bundle manifest missing before review: %s\n' "$MANIFEST_OUTPUT_FILE" >&2
    return 1
  fi
  set +e
  FUNDING_RELEASE_BUNDLE_REVIEW_FILE="$MANIFEST_OUTPUT_FILE" \
    FUNDING_RELEASE_BUNDLE_REVIEW_VALIDATION_FILE="$BUNDLE_VALIDATION_OUTPUT_FILE" \
    FUNDING_RELEASE_BUNDLE_REVIEW_FORMAT=json \
    sh "$BUNDLE_REVIEW_SCRIPT" > "$REVIEW_OUTPUT_FILE"
  review_exit=$?
  set -e
  if [ "$review_exit" -eq 0 ]; then
    printf 'Funding release bundle review written: %s\n' "$REVIEW_OUTPUT_FILE" >&2
  else
    printf 'Funding release bundle review failed: %s\n' "$REVIEW_OUTPUT_FILE" >&2
    if [ -f "$REVIEW_OUTPUT_FILE" ]; then
      cat "$REVIEW_OUTPUT_FILE" >&2
    fi
  fi
  return "$review_exit"
}

write_review_summary() {
  if [ "$FUNDING_RELEASE_CI_WRITE_SUMMARY" != "1" ]; then
    return 0
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_REVIEW" != "1" ]; then
    printf 'Funding release review summary skipped because review writing is disabled.\n' >&2
    return 0
  fi
  if [ ! -f "$REVIEW_OUTPUT_FILE" ]; then
    printf 'Funding release review artifact missing before summary: %s\n' "$REVIEW_OUTPUT_FILE" >&2
    return 1
  fi
  set +e
  FUNDING_RELEASE_REVIEW_SUMMARY_FILE="$REVIEW_OUTPUT_FILE" \
    FUNDING_RELEASE_REVIEW_SUMMARY_FORMAT=markdown \
    sh "$REVIEW_SUMMARY_SCRIPT" > "$SUMMARY_OUTPUT_FILE"
  summary_exit=$?
  set -e
  if [ "$summary_exit" -eq 0 ]; then
    printf 'Funding release review summary written: %s\n' "$SUMMARY_OUTPUT_FILE" >&2
  else
    printf 'Funding release review summary failed: %s\n' "$SUMMARY_OUTPUT_FILE" >&2
    if [ -f "$SUMMARY_OUTPUT_FILE" ]; then
      cat "$SUMMARY_OUTPUT_FILE" >&2
    fi
  fi
  return "$summary_exit"
}

write_evidence_handoff() {
  if [ "$FUNDING_RELEASE_CI_WRITE_HANDOFF" != "1" ]; then
    return 0
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_REVIEW" != "1" ]; then
    printf 'Funding release evidence handoff skipped because review writing is disabled.\n' >&2
    return 0
  fi
  if [ ! -f "$REVIEW_OUTPUT_FILE" ]; then
    printf 'Funding release review artifact missing before handoff: %s\n' "$REVIEW_OUTPUT_FILE" >&2
    return 1
  fi
  set +e
  FUNDING_RELEASE_HANDOFF_REVIEW_FILE="$REVIEW_OUTPUT_FILE" \
    FUNDING_RELEASE_HANDOFF_SUMMARY_FILE="$SUMMARY_OUTPUT_FILE" \
    FUNDING_RELEASE_HANDOFF_MANIFEST_FILE="$MANIFEST_OUTPUT_FILE" \
    FUNDING_RELEASE_HANDOFF_BUNDLE_VALIDATION_FILE="$BUNDLE_VALIDATION_OUTPUT_FILE" \
    FUNDING_RELEASE_HANDOFF_FORMAT=markdown \
    sh "$EVIDENCE_HANDOFF_SCRIPT" > "$HANDOFF_OUTPUT_FILE"
  handoff_exit=$?
  set -e
  if [ "$handoff_exit" -eq 0 ]; then
    printf 'Funding release evidence handoff written: %s\n' "$HANDOFF_OUTPUT_FILE" >&2
  else
    printf 'Funding release evidence handoff failed: %s\n' "$HANDOFF_OUTPUT_FILE" >&2
    if [ -f "$HANDOFF_OUTPUT_FILE" ]; then
      cat "$HANDOFF_OUTPUT_FILE" >&2
    fi
  fi
  return "$handoff_exit"
}

write_evidence_audit() {
  if [ "$FUNDING_RELEASE_CI_WRITE_AUDIT" != "1" ] && [ "$FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN" != "1" ]; then
    return 0
  fi
  audit_exit=0
  audit_markdown_exit=0
  if [ "$FUNDING_RELEASE_CI_WRITE_AUDIT" = "1" ]; then
    set +e
    FUNDING_RELEASE_AUDIT_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_AUDIT_FORMAT=json \
      sh "$EVIDENCE_AUDIT_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$AUDIT_OUTPUT_FILE"
    audit_exit=$?
    set -e
    if [ "$audit_exit" -eq 0 ]; then
      printf 'Funding release evidence audit written: %s\n' "$AUDIT_OUTPUT_FILE" >&2
    else
      printf 'Funding release evidence audit failed: %s\n' "$AUDIT_OUTPUT_FILE" >&2
      if [ -f "$AUDIT_OUTPUT_FILE" ]; then
        cat "$AUDIT_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_AUDIT_MARKDOWN" = "1" ]; then
    set +e
    FUNDING_RELEASE_AUDIT_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_AUDIT_FORMAT=markdown \
      sh "$EVIDENCE_AUDIT_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$AUDIT_MARKDOWN_OUTPUT_FILE"
    audit_markdown_exit=$?
    set -e
    if [ "$audit_markdown_exit" -eq 0 ]; then
      printf 'Funding release evidence audit markdown written: %s\n' "$AUDIT_MARKDOWN_OUTPUT_FILE" >&2
    else
      printf 'Funding release evidence audit markdown failed: %s\n' "$AUDIT_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$AUDIT_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$AUDIT_MARKDOWN_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$audit_exit" -ne 0 ]; then
    return "$audit_exit"
  fi
  return "$audit_markdown_exit"
}

write_evidence_index() {
  if [ "$FUNDING_RELEASE_CI_WRITE_INDEX" != "1" ] && [ "$FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN" != "1" ]; then
    return 0
  fi
  index_exit=0
  index_markdown_exit=0
  if [ "$FUNDING_RELEASE_CI_WRITE_INDEX" = "1" ]; then
    set +e
    FUNDING_RELEASE_INDEX_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_INDEX_FORMAT=json \
      sh "$EVIDENCE_INDEX_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$INDEX_OUTPUT_FILE"
    index_exit=$?
    set -e
    if [ "$index_exit" -eq 0 ]; then
      printf 'Funding release evidence index written: %s\n' "$INDEX_OUTPUT_FILE" >&2
    else
      printf 'Funding release evidence index failed: %s\n' "$INDEX_OUTPUT_FILE" >&2
      if [ -f "$INDEX_OUTPUT_FILE" ]; then
        cat "$INDEX_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_INDEX_MARKDOWN" = "1" ]; then
    set +e
    FUNDING_RELEASE_INDEX_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_INDEX_FORMAT=markdown \
      sh "$EVIDENCE_INDEX_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$INDEX_MARKDOWN_OUTPUT_FILE"
    index_markdown_exit=$?
    set -e
    if [ "$index_markdown_exit" -eq 0 ]; then
      printf 'Funding release evidence index markdown written: %s\n' "$INDEX_MARKDOWN_OUTPUT_FILE" >&2
    else
      printf 'Funding release evidence index markdown failed: %s\n' "$INDEX_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$INDEX_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$INDEX_MARKDOWN_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$index_exit" -ne 0 ]; then
    return "$index_exit"
  fi
  return "$index_markdown_exit"
}

write_evidence_verify() {
  if [ "$FUNDING_RELEASE_CI_WRITE_VERIFY" != "1" ] && [ "$FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN" != "1" ]; then
    return 0
  fi
  verify_exit=0
  verify_markdown_exit=0
  if [ "$FUNDING_RELEASE_CI_WRITE_VERIFY" = "1" ]; then
    set +e
    FUNDING_RELEASE_VERIFY_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_VERIFY_FORMAT=json \
      sh "$EVIDENCE_VERIFY_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$VERIFY_OUTPUT_FILE"
    verify_exit=$?
    set -e
    if [ "$verify_exit" -eq 0 ]; then
      printf 'Funding release evidence verify written: %s\n' "$VERIFY_OUTPUT_FILE" >&2
    elif [ "$verify_exit" -eq 2 ]; then
      printf 'Funding release evidence verify blocked: %s\n' "$VERIFY_OUTPUT_FILE" >&2
      if [ -f "$VERIFY_OUTPUT_FILE" ]; then
        cat "$VERIFY_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence verify failed: %s\n' "$VERIFY_OUTPUT_FILE" >&2
      if [ -f "$VERIFY_OUTPUT_FILE" ]; then
        cat "$VERIFY_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_VERIFY_MARKDOWN" = "1" ]; then
    set +e
    FUNDING_RELEASE_VERIFY_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_VERIFY_FORMAT=markdown \
      sh "$EVIDENCE_VERIFY_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$VERIFY_MARKDOWN_OUTPUT_FILE"
    verify_markdown_exit=$?
    set -e
    if [ "$verify_markdown_exit" -eq 0 ]; then
      printf 'Funding release evidence verify markdown written: %s\n' "$VERIFY_MARKDOWN_OUTPUT_FILE" >&2
    elif [ "$verify_markdown_exit" -eq 2 ]; then
      printf 'Funding release evidence verify markdown blocked: %s\n' "$VERIFY_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$VERIFY_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$VERIFY_MARKDOWN_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence verify markdown failed: %s\n' "$VERIFY_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$VERIFY_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$VERIFY_MARKDOWN_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$verify_exit" -ne 0 ]; then
    return "$verify_exit"
  fi
  return "$verify_markdown_exit"
}

write_evidence_notes() {
  if [ "$FUNDING_RELEASE_CI_WRITE_NOTES" != "1" ] && [ "$FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN" != "1" ]; then
    return 0
  fi
  notes_exit=0
  notes_markdown_exit=0
  if [ "$FUNDING_RELEASE_CI_WRITE_NOTES" = "1" ]; then
    set +e
    FUNDING_RELEASE_NOTES_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_NOTES_FORMAT=json \
      sh "$EVIDENCE_NOTES_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$NOTES_OUTPUT_FILE"
    notes_exit=$?
    set -e
    if [ "$notes_exit" -eq 0 ]; then
      printf 'Funding release evidence notes written: %s\n' "$NOTES_OUTPUT_FILE" >&2
    elif [ "$notes_exit" -eq 2 ]; then
      printf 'Funding release evidence notes blocked: %s\n' "$NOTES_OUTPUT_FILE" >&2
      if [ -f "$NOTES_OUTPUT_FILE" ]; then
        cat "$NOTES_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence notes failed: %s\n' "$NOTES_OUTPUT_FILE" >&2
      if [ -f "$NOTES_OUTPUT_FILE" ]; then
        cat "$NOTES_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_NOTES_MARKDOWN" = "1" ]; then
    set +e
    FUNDING_RELEASE_NOTES_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_NOTES_FORMAT=markdown \
      sh "$EVIDENCE_NOTES_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$NOTES_MARKDOWN_OUTPUT_FILE"
    notes_markdown_exit=$?
    set -e
    if [ "$notes_markdown_exit" -eq 0 ]; then
      printf 'Funding release evidence notes markdown written: %s\n' "$NOTES_MARKDOWN_OUTPUT_FILE" >&2
    elif [ "$notes_markdown_exit" -eq 2 ]; then
      printf 'Funding release evidence notes markdown blocked: %s\n' "$NOTES_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$NOTES_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$NOTES_MARKDOWN_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence notes markdown failed: %s\n' "$NOTES_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$NOTES_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$NOTES_MARKDOWN_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$notes_exit" -ne 0 ]; then
    return "$notes_exit"
  fi
  return "$notes_markdown_exit"
}

write_evidence_archive() {
  if [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE" != "1" ] && [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN" != "1" ]; then
    return 0
  fi
  archive_exit=0
  archive_markdown_exit=0
  if [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE" = "1" ]; then
    set +e
    FUNDING_RELEASE_ARCHIVE_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_ARCHIVE_FORMAT=json \
      sh "$EVIDENCE_ARCHIVE_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$ARCHIVE_OUTPUT_FILE"
    archive_exit=$?
    set -e
    if [ "$archive_exit" -eq 0 ]; then
      printf 'Funding release evidence archive written: %s\n' "$ARCHIVE_OUTPUT_FILE" >&2
    elif [ "$archive_exit" -eq 2 ]; then
      printf 'Funding release evidence archive blocked: %s\n' "$ARCHIVE_OUTPUT_FILE" >&2
      if [ -f "$ARCHIVE_OUTPUT_FILE" ]; then
        cat "$ARCHIVE_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence archive failed: %s\n' "$ARCHIVE_OUTPUT_FILE" >&2
      if [ -f "$ARCHIVE_OUTPUT_FILE" ]; then
        cat "$ARCHIVE_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$FUNDING_RELEASE_CI_WRITE_ARCHIVE_MARKDOWN" = "1" ]; then
    set +e
    FUNDING_RELEASE_ARCHIVE_DIR="$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
      FUNDING_RELEASE_ARCHIVE_FORMAT=markdown \
      sh "$EVIDENCE_ARCHIVE_SCRIPT" "$FUNDING_RELEASE_CI_ARTIFACT_DIR" > "$ARCHIVE_MARKDOWN_OUTPUT_FILE"
    archive_markdown_exit=$?
    set -e
    if [ "$archive_markdown_exit" -eq 0 ]; then
      printf 'Funding release evidence archive markdown written: %s\n' "$ARCHIVE_MARKDOWN_OUTPUT_FILE" >&2
    elif [ "$archive_markdown_exit" -eq 2 ]; then
      printf 'Funding release evidence archive markdown blocked: %s\n' "$ARCHIVE_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$ARCHIVE_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$ARCHIVE_MARKDOWN_OUTPUT_FILE" >&2
      fi
    else
      printf 'Funding release evidence archive markdown failed: %s\n' "$ARCHIVE_MARKDOWN_OUTPUT_FILE" >&2
      if [ -f "$ARCHIVE_MARKDOWN_OUTPUT_FILE" ]; then
        cat "$ARCHIVE_MARKDOWN_OUTPUT_FILE" >&2
      fi
    fi
  fi
  if [ "$archive_exit" -ne 0 ]; then
    return "$archive_exit"
  fi
  return "$archive_markdown_exit"
}

write_ci_status() {
  report_exit="$1"
  validation_exit="$2"
  bundle_validation_exit="$3"
  review_exit="$4"
  summary_exit="$5"
  handoff_exit="$6"
  audit_exit="$7"
  index_exit="$8"
  verify_exit="$9"
  shift 9
  notes_exit="$1"
  archive_exit="$2"
  final_stage="$3"
  final_exit="$4"

  if [ "$FUNDING_RELEASE_CI_WRITE_STATUS" != "1" ]; then
    return 0
  fi

  "$PYTHON_BIN" - \
    "$STATUS_OUTPUT_FILE" \
    "$FUNDING_RELEASE_CI_ARTIFACT_DIR" \
    "$FUNDING_RELEASE_REPORT_OUTPUT" \
    "$VALIDATION_OUTPUT_FILE" \
    "$MANIFEST_OUTPUT_FILE" \
    "$BUNDLE_VALIDATION_OUTPUT_FILE" \
    "$REVIEW_OUTPUT_FILE" \
    "$SUMMARY_OUTPUT_FILE" \
    "$HANDOFF_OUTPUT_FILE" \
    "$AUDIT_OUTPUT_FILE" \
    "$AUDIT_MARKDOWN_OUTPUT_FILE" \
    "$INDEX_OUTPUT_FILE" \
    "$INDEX_MARKDOWN_OUTPUT_FILE" \
    "$VERIFY_OUTPUT_FILE" \
    "$VERIFY_MARKDOWN_OUTPUT_FILE" \
    "$NOTES_OUTPUT_FILE" \
    "$NOTES_MARKDOWN_OUTPUT_FILE" \
    "$ARCHIVE_OUTPUT_FILE" \
    "$ARCHIVE_MARKDOWN_OUTPUT_FILE" \
    "$FUNDING_RELEASE_CI_STDOUT_FILE" \
    "$report_exit" \
    "$validation_exit" \
    "$bundle_validation_exit" \
    "$review_exit" \
    "$summary_exit" \
    "$handoff_exit" \
    "$audit_exit" \
    "$index_exit" \
    "$verify_exit" \
    "$notes_exit" \
    "$archive_exit" \
    "$final_stage" \
    "$final_exit" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

(
    status_path_raw,
    artifact_dir_raw,
    report_path_raw,
    validation_path_raw,
    manifest_path_raw,
    bundle_validation_path_raw,
    review_path_raw,
    summary_path_raw,
    handoff_path_raw,
    audit_path_raw,
    audit_markdown_path_raw,
    index_path_raw,
    index_markdown_path_raw,
    verify_path_raw,
    verify_markdown_path_raw,
    notes_path_raw,
    notes_markdown_path_raw,
    archive_path_raw,
    archive_markdown_path_raw,
    stdout_path_raw,
    report_exit_raw,
    validation_exit_raw,
    bundle_validation_exit_raw,
    review_exit_raw,
    summary_exit_raw,
    handoff_exit_raw,
    audit_exit_raw,
    index_exit_raw,
    verify_exit_raw,
    notes_exit_raw,
    archive_exit_raw,
    final_stage,
    final_exit_raw,
) = sys.argv[1:34]

status_path = Path(status_path_raw)
artifact_dir = Path(artifact_dir_raw)
paths = {
    "report": Path(report_path_raw),
    "validation": Path(validation_path_raw),
    "manifest": Path(manifest_path_raw),
    "bundle_validation": Path(bundle_validation_path_raw),
    "review": Path(review_path_raw),
    "summary": Path(summary_path_raw),
    "handoff": Path(handoff_path_raw),
    "audit": Path(audit_path_raw),
    "audit_markdown": Path(audit_markdown_path_raw),
    "index": Path(index_path_raw),
    "index_markdown": Path(index_markdown_path_raw),
    "verify": Path(verify_path_raw),
    "verify_markdown": Path(verify_markdown_path_raw),
    "notes": Path(notes_path_raw),
    "notes_markdown": Path(notes_markdown_path_raw),
    "archive": Path(archive_path_raw),
    "archive_markdown": Path(archive_markdown_path_raw),
    "stdout": Path(stdout_path_raw) if stdout_path_raw else None,
}
stage_exit_codes = {
    "report": int(report_exit_raw),
    "validation": int(validation_exit_raw),
    "bundle_validation": int(bundle_validation_exit_raw),
    "review": int(review_exit_raw),
    "summary": int(summary_exit_raw),
    "handoff": int(handoff_exit_raw),
    "audit": int(audit_exit_raw),
    "index": int(index_exit_raw),
    "verify": int(verify_exit_raw),
    "notes": int(notes_exit_raw),
    "archive": int(archive_exit_raw),
}
final_exit_code = int(final_exit_raw)

def read_json(path):
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}

def file_info(path):
    if path is None:
        return {"configured": False, "path": None, "exists": False}
    return {
        "configured": True,
        "path": str(path),
        "exists": path.is_file(),
    }

report = read_json(paths["report"])
manifest = read_json(paths["manifest"])
validation = read_json(paths["validation"])
bundle_validation = read_json(paths["bundle_validation"])
review = read_json(paths["review"])
audit = read_json(paths["audit"])
index = read_json(paths["index"])
verify = read_json(paths["verify"])
notes = read_json(paths["notes"])
archive = read_json(paths["archive"])

run_context = {}
for source in (report, manifest):
    candidate = source.get("run_context")
    if isinstance(candidate, dict):
        run_context = candidate
        break

if final_exit_code == 0:
    final_status = "passed"
elif final_exit_code == 2 or final_stage in {"report", "verify", "notes", "archive"}:
    final_status = "blocked"
else:
    final_status = "failed"

status = {
    "ci_status_version": "funding_release_ci_status_v0",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "artifact_dir": str(artifact_dir),
    "final_status": final_status,
    "final_exit_code": final_exit_code,
    "final_stage": final_stage,
    "stage_exit_codes": stage_exit_codes,
    "artifact_status": {
        "release_gate_status": report.get("release_gate_status") or review.get("release_gate_status"),
        "report_exit_code": report.get("report_exit_code"),
        "exit_reason": report.get("exit_reason") or review.get("exit_reason"),
        "readiness_gate_status": report.get("readiness_gate_status") or review.get("readiness_gate_status"),
        "compare_gate_status": report.get("compare_gate_status") or review.get("compare_gate_status"),
        "validation_status": validation.get("status"),
        "bundle_exit_code": manifest.get("bundle_exit_code"),
        "bundle_validation_status": bundle_validation.get("status"),
        "review_status": review.get("review_status"),
        "recommended_next_action": review.get("recommended_next_action"),
        "audit_status": audit.get("audit_status"),
        "index_status": index.get("index_status"),
        "verification_status": verify.get("verification_status"),
        "blocking_mode": verify.get("blocking_mode"),
        "release_notes_ready": verify.get("release_notes_ready"),
        "debug_review_ready": verify.get("debug_review_ready"),
        "notes_status": notes.get("notes_status"),
        "notes_mode": notes.get("notes_mode"),
        "archive_status": archive.get("archive_status"),
        "archive_mode": archive.get("archive_mode"),
        "archive_missing_required_count": archive.get("missing_required_count"),
        "archive_error_count": archive.get("error_count"),
    },
    "run_context": run_context,
    "files": {name: file_info(path) for name, path in paths.items()},
}

status_path.parent.mkdir(parents=True, exist_ok=True)
status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
  printf 'Funding release CI status written: %s\n' "$STATUS_OUTPUT_FILE" >&2
}

finish_ci_run() {
  report_exit="$1"
  validation_exit="$2"
  bundle_validation_exit="$3"
  review_exit="$4"
  summary_exit="$5"
  handoff_exit="$6"
  audit_exit="$7"
  index_exit="$8"
  verify_exit="$9"
  shift 9
  notes_exit="$1"
  archive_exit="$2"

  final_stage="report"
  final_exit="$report_exit"
  if [ "$validation_exit" -ne 0 ]; then
    final_stage="validation"
    final_exit="$validation_exit"
  elif [ "$bundle_validation_exit" -ne 0 ]; then
    final_stage="bundle_validation"
    final_exit="$bundle_validation_exit"
  elif [ "$review_exit" -ne 0 ]; then
    final_stage="review"
    final_exit="$review_exit"
  elif [ "$summary_exit" -ne 0 ]; then
    final_stage="summary"
    final_exit="$summary_exit"
  elif [ "$handoff_exit" -ne 0 ]; then
    final_stage="handoff"
    final_exit="$handoff_exit"
  elif [ "$audit_exit" -ne 0 ]; then
    final_stage="audit"
    final_exit="$audit_exit"
  elif [ "$index_exit" -ne 0 ]; then
    final_stage="index"
    final_exit="$index_exit"
  elif [ "$verify_exit" -ne 0 ]; then
    final_stage="verify"
    final_exit="$verify_exit"
  elif [ "$notes_exit" -ne 0 ]; then
    final_stage="notes"
    final_exit="$notes_exit"
  elif [ "$archive_exit" -ne 0 ]; then
    final_stage="archive"
    final_exit="$archive_exit"
  fi

  set +e
  write_ci_status \
    "$report_exit" \
    "$validation_exit" \
    "$bundle_validation_exit" \
    "$review_exit" \
    "$summary_exit" \
    "$handoff_exit" \
    "$audit_exit" \
    "$index_exit" \
    "$verify_exit" \
    "$notes_exit" \
    "$archive_exit" \
    "$final_stage" \
    "$final_exit"
  status_exit=$?
  set -e
  if [ "$status_exit" -ne 0 ]; then
    printf 'Funding release CI status failed: %s\n' "$STATUS_OUTPUT_FILE" >&2
    if [ "$final_exit" -eq 0 ]; then
      exit "$status_exit"
    fi
  fi
  exit "$final_exit"
}

if [ -n "$FUNDING_RELEASE_CI_STDOUT_FILE" ]; then
  set +e
  sh "$REPORT_SCRIPT" > "$FUNDING_RELEASE_CI_STDOUT_FILE"
  REPORT_EXIT=$?
  set -e
  cat "$FUNDING_RELEASE_CI_STDOUT_FILE"
  set +e
  validate_report_artifact "$REPORT_EXIT"
  VALIDATE_EXIT=$?
  set -e
  write_bundle_manifest "$REPORT_EXIT" "$VALIDATE_EXIT"
  set +e
  validate_bundle_manifest
  BUNDLE_VALIDATE_EXIT=$?
  set -e
  set +e
  write_bundle_review
  REVIEW_EXIT=$?
  set -e
  set +e
  write_review_summary
  SUMMARY_EXIT=$?
  set -e
  set +e
  write_evidence_handoff
  HANDOFF_EXIT=$?
  set -e
  set +e
  write_evidence_audit
  AUDIT_EXIT=$?
  set -e
  set +e
  write_evidence_index
  INDEX_EXIT=$?
  set -e
  set +e
  write_evidence_verify
  VERIFY_EXIT=$?
  set -e
  set +e
  write_evidence_notes
  NOTES_EXIT=$?
  set -e
  set +e
  write_evidence_archive
  ARCHIVE_EXIT=$?
  set -e
  finish_ci_run \
    "$REPORT_EXIT" \
    "$VALIDATE_EXIT" \
    "$BUNDLE_VALIDATE_EXIT" \
    "$REVIEW_EXIT" \
    "$SUMMARY_EXIT" \
    "$HANDOFF_EXIT" \
    "$AUDIT_EXIT" \
    "$INDEX_EXIT" \
    "$VERIFY_EXIT" \
    "$NOTES_EXIT" \
    "$ARCHIVE_EXIT"
fi

set +e
sh "$REPORT_SCRIPT"
REPORT_EXIT=$?
set -e
set +e
validate_report_artifact "$REPORT_EXIT"
VALIDATE_EXIT=$?
set -e
write_bundle_manifest "$REPORT_EXIT" "$VALIDATE_EXIT"
set +e
validate_bundle_manifest
BUNDLE_VALIDATE_EXIT=$?
set -e
set +e
write_bundle_review
REVIEW_EXIT=$?
set -e
set +e
write_review_summary
SUMMARY_EXIT=$?
set -e
set +e
write_evidence_handoff
HANDOFF_EXIT=$?
set -e
set +e
write_evidence_audit
AUDIT_EXIT=$?
set -e
set +e
write_evidence_index
INDEX_EXIT=$?
set -e
set +e
write_evidence_verify
VERIFY_EXIT=$?
set -e
set +e
write_evidence_notes
NOTES_EXIT=$?
set -e
set +e
write_evidence_archive
ARCHIVE_EXIT=$?
set -e
finish_ci_run \
  "$REPORT_EXIT" \
  "$VALIDATE_EXIT" \
  "$BUNDLE_VALIDATE_EXIT" \
  "$REVIEW_EXIT" \
  "$SUMMARY_EXIT" \
  "$HANDOFF_EXIT" \
  "$AUDIT_EXIT" \
  "$INDEX_EXIT" \
  "$VERIFY_EXIT" \
  "$NOTES_EXIT" \
  "$ARCHIVE_EXIT"
