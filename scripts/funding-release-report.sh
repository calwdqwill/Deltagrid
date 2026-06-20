#!/usr/bin/env sh
set -u

case "$0" in
  */*) SCRIPT_DIR=${0%/*} ;;
  *) SCRIPT_DIR=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR" && pwd)
RELEASE_SMOKE_SCRIPT="$SCRIPT_DIR/funding-release-smoke.sh"

PYTHON_BIN="${PYTHON_BIN:-python3}"
REPORT_JSON_FILE="${FUNDING_RELEASE_REPORT_JSON:-${TMPDIR:-/tmp}/deltagrid-funding-release-report-$$.json}"
KEEP_REPORT_JSON="${KEEP_FUNDING_RELEASE_REPORT_JSON:-0}"
REPORT_OUTPUT_FILE="${FUNDING_RELEASE_REPORT_OUTPUT:-}"
REPORT_PROFILE="${FUNDING_RELEASE_REPORT_PROFILE:-manual}"
if [ "$REPORT_PROFILE" = "ci" ]; then
  REPORT_FORMAT="${FUNDING_RELEASE_REPORT_FORMAT:-json}"
  REPORT_REQUIRE_READY="${FUNDING_RELEASE_REPORT_REQUIRE_READY:-1}"
  REPORT_REQUIRE_COMPARE="${FUNDING_RELEASE_REPORT_REQUIRE_COMPARE:-1}"
else
  REPORT_FORMAT="${FUNDING_RELEASE_REPORT_FORMAT:-text}"
  REPORT_REQUIRE_READY="${FUNDING_RELEASE_REPORT_REQUIRE_READY:-0}"
  REPORT_REQUIRE_COMPARE="${FUNDING_RELEASE_REPORT_REQUIRE_COMPARE:-0}"
fi
REPORT_STRICT_MODE="${FUNDING_RELEASE_STRICT:-${RELEASE_STRICT:-0}}"
REPORT_FAIL_ON_DIFF="${FAIL_ON_DIFF:-}"
REPORT_FAIL_ON_RELEASE_NOT_READY="${FAIL_ON_RELEASE_NOT_READY:-}"

path_parent_dir() {
  case "$1" in
    /*/*) printf '%s\n' "${1%/*}" ;;
    /*) printf '/\n' ;;
    */*) printf '%s\n' "${1%/*}" ;;
    *) printf '.\n' ;;
  esac
}

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

require_non_negative_int() {
  name="$1"
  value="$2"
  case "$value" in
    ''|*[!0-9]*)
      printf '%s must be a non-negative integer.\n' "$name" >&2
      exit 1
      ;;
  esac
}

validate_output_file_path() {
  name="$1"
  value="$2"
  [ -z "$value" ] && return 0
  if [ -d "$value" ]; then
    printf '%s must be a file path, got directory: %s\n' "$name" "$value" >&2
    exit 4
  fi
  parent_dir=$(path_parent_dir "$value")
  if [ ! -d "$parent_dir" ]; then
    printf '%s parent directory does not exist: %s\n' "$name" "$parent_dir" >&2
    exit 4
  fi
}

if [ "$REPORT_STRICT_MODE" = "1" ]; then
  REPORT_FAIL_ON_DIFF="${REPORT_FAIL_ON_DIFF:-1}"
  REPORT_FAIL_ON_RELEASE_NOT_READY="${REPORT_FAIL_ON_RELEASE_NOT_READY:-1}"
else
  REPORT_FAIL_ON_DIFF="${REPORT_FAIL_ON_DIFF:-0}"
  REPORT_FAIL_ON_RELEASE_NOT_READY="${REPORT_FAIL_ON_RELEASE_NOT_READY:-0}"
fi

cleanup() {
  if [ "$KEEP_REPORT_JSON" != "1" ] && [ -f "$REPORT_JSON_FILE" ]; then
    if "$PYTHON_BIN" --version >/dev/null 2>&1; then
      "$PYTHON_BIN" - "$REPORT_JSON_FILE" <<'PY' >/dev/null 2>&1 || true
import os
import sys

try:
    os.remove(sys.argv[1])
except FileNotFoundError:
    pass
PY
    fi
  fi
}
trap cleanup EXIT HUP INT TERM

if [ ! -f "$RELEASE_SMOKE_SCRIPT" ]; then
  printf 'Missing Funding release smoke script: %s\n' "$RELEASE_SMOKE_SCRIPT" >&2
  exit 1
fi

case "$REPORT_PROFILE" in
  manual|ci) ;;
  *)
    printf 'FUNDING_RELEASE_REPORT_PROFILE must be manual or ci.\n' >&2
    exit 1
    ;;
esac

case "$REPORT_FORMAT" in
  text|json) ;;
  *)
    printf 'FUNDING_RELEASE_REPORT_FORMAT must be text or json.\n' >&2
    exit 1
    ;;
esac

case "$REPORT_REQUIRE_READY" in
  0|1) ;;
  *)
    printf 'FUNDING_RELEASE_REPORT_REQUIRE_READY must be 0 or 1.\n' >&2
    exit 1
    ;;
esac

case "$REPORT_REQUIRE_COMPARE" in
  0|1) ;;
  *)
    printf 'FUNDING_RELEASE_REPORT_REQUIRE_COMPARE must be 0 or 1.\n' >&2
    exit 1
    ;;
esac

require_bool "FUNDING_RELEASE_STRICT" "$REPORT_STRICT_MODE"
require_bool "FAIL_ON_DIFF" "$REPORT_FAIL_ON_DIFF"
require_bool "FAIL_ON_RELEASE_NOT_READY" "$REPORT_FAIL_ON_RELEASE_NOT_READY"
require_bool "RUN_FRONTEND_CHECK" "${RUN_FRONTEND_CHECK:-1}"
require_bool "KEEP_FUNDING_RELEASE_REPORT_JSON" "$KEEP_REPORT_JSON"
require_non_negative_int "MIN_TOTAL_ROWS" "${MIN_TOTAL_ROWS:-1}"
validate_output_file_path "FUNDING_RELEASE_REPORT_JSON" "$REPORT_JSON_FILE"
validate_output_file_path "FUNDING_RELEASE_REPORT_OUTPUT" "$REPORT_OUTPUT_FILE"

if [ -n "$REPORT_OUTPUT_FILE" ] && [ "$REPORT_OUTPUT_FILE" = "$REPORT_JSON_FILE" ]; then
  printf 'FUNDING_RELEASE_REPORT_OUTPUT must differ from FUNDING_RELEASE_REPORT_JSON.\n' >&2
  exit 4
fi

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release report.\n' >&2
    exit 1
  fi
fi

set +e
(
  OUTPUT_JSON_ONLY=1
  export OUTPUT_JSON_ONLY
  . "$RELEASE_SMOKE_SCRIPT"
) > "$REPORT_JSON_FILE"
SMOKE_EXIT=$?
set -e

if [ ! -s "$REPORT_JSON_FILE" ]; then
  printf 'Funding release report unavailable; smoke_exit=%s\n' "$SMOKE_EXIT" >&2
  exit "$SMOKE_EXIT"
fi

"$PYTHON_BIN" - "$REPORT_JSON_FILE" "$SMOKE_EXIT" "$REPORT_FORMAT" "$REPORT_PROFILE" "$REPORT_REQUIRE_READY" "$REPORT_REQUIRE_COMPARE" "${BASE_URL:-http://127.0.0.1:8000}" "${FRONTEND_URL:-http://127.0.0.1:3001}" "${COMPARE_BASE_URL:-}" "$REPORT_STRICT_MODE" "$REPORT_FAIL_ON_DIFF" "$REPORT_FAIL_ON_RELEASE_NOT_READY" "${RUN_FRONTEND_CHECK:-1}" "${MIN_TOTAL_ROWS:-1}" "$REPORT_OUTPUT_FILE" <<'PY'
import json
import os
import sys

(
    json_path,
    smoke_exit_raw,
    report_format,
    report_profile,
    report_require_ready_raw,
    report_require_compare_raw,
    requested_base_url,
    requested_frontend_url,
    requested_compare_base_url,
    strict_mode_raw,
    fail_on_diff_raw,
    fail_on_release_not_ready_raw,
    run_frontend_check_raw,
    min_total_rows_raw,
    requested_report_output_file,
) = sys.argv[1:16]
smoke_exit = int(smoke_exit_raw)

try:
    with open(json_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
except (OSError, json.JSONDecodeError) as exc:
    print(f"Funding release report parse failed: {exc}", file=sys.stderr)
    raise SystemExit(1)

contract = payload.get("contract") if isinstance(payload, dict) else {}
contract = contract if isinstance(contract, dict) else {}
readiness = contract.get("release_readiness")
readiness = readiness if isinstance(readiness, dict) else {}
compare = payload.get("compare") if isinstance(payload, dict) else {}
compare = compare if isinstance(compare, dict) else {}
compare_summary = compare.get("summary")
compare_summary = compare_summary if isinstance(compare_summary, dict) else {}
safety_flags = contract.get("safety_flags")
safety_flags = safety_flags if isinstance(safety_flags, dict) else {}
source_rows = contract.get("funding_rows_by_source")
source_rows = source_rows if isinstance(source_rows, dict) else {}
source_pair_statuses = contract.get("source_pair_statuses")
source_pair_statuses = source_pair_statuses if isinstance(source_pair_statuses, dict) else {}
data_quality_runway = contract.get("data_quality_runway")
data_quality_runway = data_quality_runway if isinstance(data_quality_runway, dict) else {}
readiness_checks = readiness.get("checks")
readiness_checks = readiness_checks if isinstance(readiness_checks, dict) else {}

forbidden_flags = [
    "trading_enabled",
    "execution_enabled",
    "route_ranking_enabled",
    "route_selection_enabled",
    "numeric_route_cost_bps_enabled",
    "diagnostic_carry_bps_enabled",
]
unsafe_flags = [
    flag for flag in forbidden_flags
    if safety_flags.get(flag) is not False
]
safety_status = "locked" if not unsafe_flags else "unsafe"

missing_frontend = readiness.get("missing_frontend_markers")
missing_frontend = missing_frontend if isinstance(missing_frontend, list) else []
sources_with_rows = readiness.get("sources_with_rows")
sources_with_rows = sources_with_rows if isinstance(sources_with_rows, list) else []

source_row_text = ", ".join(
    f"{key}={source_rows[key]}" for key in sorted(source_rows)
) or "none"
source_pair_text = ", ".join(
    f"{key}={source_pair_statuses[key]}" for key in sorted(source_pair_statuses)
) or "none"
compare_status = compare_summary.get("status") or "not_run"
compare_gate_status = "aligned" if compare_status == "aligned" else compare_status
diff_count = compare_summary.get("diff_count")
diff_count_text = "n/a" if diff_count is None else str(diff_count)
compare_diff_fields = compare_summary.get("diff_fields")
compare_diff_fields = compare_diff_fields if isinstance(compare_diff_fields, list) else []
compare_diff_text = ", ".join(str(field) for field in compare_diff_fields) or "none"
gate_status = "passed" if smoke_exit == 0 else "failed"

readiness_check_statuses = {}
readiness_check_next_actions = {}
for key, value in sorted(readiness_checks.items()):
    if isinstance(value, dict):
        readiness_check_statuses[key] = value.get("status", "unknown")
        readiness_check_next_actions[key] = value.get("next_action", "unknown")
    else:
        readiness_check_statuses[key] = "unknown"
        readiness_check_next_actions[key] = "unknown"
readiness_check_text = ", ".join(
    f"{key}={value}" for key, value in readiness_check_statuses.items()
) or "none"
sources_with_rows_text = ", ".join(str(source) for source in sources_with_rows) or "none"
readiness_status = readiness.get("status", "unknown")
readiness_next_action = readiness.get("next_action", "unknown")
readiness_gate_status = "ready" if readiness_status == "ready_for_preview_smoke" else "not_ready"
runway_status = data_quality_runway.get("status", "unknown")
runway_next_action = data_quality_runway.get("next_action", "unknown")
runway_blocking_gate_ids = data_quality_runway.get("blocking_gate_ids")
runway_blocking_gate_ids = runway_blocking_gate_ids if isinstance(runway_blocking_gate_ids, list) else []
ready_statuses_by_check = {
    "data_health": {"ready"},
    "funding_rows": {"loaded"},
    "source_coverage": {"both_sources_loaded"},
    "frontend_markers": {"ready"},
    "compare_support": {"ready"},
    "safety_boundary": {"locked"},
}
blocking_reasons = []
if readiness_gate_status != "ready":
    blocking_reasons.append(f"release_readiness={readiness_status}")
if runway_status == "blocked":
    blocking_reasons.append("data_quality_runway=blocked")
for key, status in readiness_check_statuses.items():
    ready_statuses = ready_statuses_by_check.get(key)
    if ready_statuses and status not in ready_statuses:
        blocking_reasons.append(f"{key}={status}")
blocking_text = ", ".join(blocking_reasons) or "none"

next_actions = []
if readiness_next_action and readiness_next_action != "unknown":
    next_actions.append(readiness_next_action)
if runway_status in {"blocked", "needs_review"} and runway_next_action and runway_next_action != "unknown":
    next_actions.append(runway_next_action)
for key, action in readiness_check_next_actions.items():
    status = readiness_check_statuses.get(key, "unknown")
    ready_statuses = ready_statuses_by_check.get(key)
    if ready_statuses and status not in ready_statuses and action and action != "unknown":
        next_actions.append(action)
deduped_next_actions = []
for action in next_actions:
    if action not in deduped_next_actions:
        deduped_next_actions.append(action)
next_action_text = "; ".join(deduped_next_actions) or "none"

def flag(value):
    return value == "1"

def env_value(name):
    value = os.environ.get(name)
    return value if value else None

ci_provider = "local"
if os.environ.get("GITHUB_ACTIONS") == "true":
    ci_provider = "github_actions"
elif os.environ.get("CI") == "true":
    ci_provider = "generic_ci"

ci_context = {
    "is_ci": ci_provider != "local",
    "provider": ci_provider,
    "github": {
        "repository": env_value("GITHUB_REPOSITORY"),
        "workflow": env_value("GITHUB_WORKFLOW"),
        "job": env_value("GITHUB_JOB"),
        "run_id": env_value("GITHUB_RUN_ID"),
        "run_attempt": env_value("GITHUB_RUN_ATTEMPT"),
        "ref": env_value("GITHUB_REF"),
        "sha": env_value("GITHUB_SHA"),
        "actor": env_value("GITHUB_ACTOR"),
        "server_url": env_value("GITHUB_SERVER_URL"),
    },
}

report_require_ready = flag(report_require_ready_raw)
report_require_compare = flag(report_require_compare_raw)

try:
    min_total_rows = int(min_total_rows_raw)
except ValueError:
    min_total_rows = min_total_rows_raw

report_exit_code = smoke_exit
exit_reason = "smoke_failed" if smoke_exit != 0 else "passed"
if smoke_exit == 0 and report_require_ready and readiness_gate_status != "ready":
    report_exit_code = 2
    exit_reason = "readiness_not_ready"
elif smoke_exit == 0 and report_require_compare and compare_gate_status != "aligned":
    report_exit_code = 3
    exit_reason = "compare_not_aligned"
release_gate_status = "passed"
if exit_reason == "smoke_failed":
    release_gate_status = "failed"
elif exit_reason != "passed":
    release_gate_status = "blocked"

def clean_action(value):
    if value and value != "unknown":
        return value
    return "none"

gate_check_categories = {
    "smoke_contract": "smoke",
    "release_readiness": "readiness",
    "data_quality_runway": "readiness",
    "compare_alignment": "compare",
    "data_health": "data",
    "funding_rows": "data",
    "source_coverage": "data",
    "frontend_markers": "frontend",
    "safety_boundary": "safety",
    "report_profile": "run_context",
}

def add_gate_check(checks, check_id, status, required=False, blocking=False, next_action="none"):
    checks.append({
        "id": check_id,
        "category": gate_check_categories.get(check_id, "general"),
        "status": status,
        "required": required,
        "blocking": blocking,
        "next_action": clean_action(next_action),
    })

release_gate_checks = []
add_gate_check(
    release_gate_checks,
    "smoke_contract",
    gate_status,
    required=True,
    blocking=smoke_exit != 0,
    next_action="Inspect funding QA smoke failure" if smoke_exit != 0 else "none",
)
add_gate_check(
    release_gate_checks,
    "release_readiness",
    readiness_gate_status,
    required=report_require_ready,
    blocking=report_require_ready and readiness_gate_status != "ready",
    next_action=readiness_next_action,
)
add_gate_check(
    release_gate_checks,
    "data_quality_runway",
    runway_status,
    required=report_require_ready,
    blocking=report_require_ready and runway_status == "blocked",
    next_action=runway_next_action,
)
add_gate_check(
    release_gate_checks,
    "compare_alignment",
    compare_gate_status,
    required=report_require_compare,
    blocking=report_require_compare and compare_gate_status != "aligned",
    next_action="Set COMPARE_BASE_URL and resolve compare drift" if compare_gate_status != "aligned" else "none",
)
for check_id in [
    "data_health",
    "funding_rows",
    "source_coverage",
    "frontend_markers",
    "safety_boundary",
]:
    status = readiness_check_statuses.get(check_id, "unknown")
    ready_statuses = ready_statuses_by_check.get(check_id, set())
    is_blocking = check_id in {"data_health", "funding_rows", "source_coverage", "safety_boundary"} and status not in ready_statuses
    if check_id == "frontend_markers":
        is_blocking = flag(run_frontend_check_raw) and status not in ready_statuses
    is_required = check_id == "safety_boundary" or (
        report_require_ready and (check_id != "frontend_markers" or flag(run_frontend_check_raw))
    )
    add_gate_check(
        release_gate_checks,
        check_id,
        status,
        required=is_required,
        blocking=is_blocking,
        next_action=readiness_check_next_actions.get(check_id, "none"),
    )
add_gate_check(
    release_gate_checks,
    "report_profile",
    report_profile,
    required=False,
    blocking=False,
    next_action="none",
)

release_gate_blocking_ids = [
    check["id"] for check in release_gate_checks if check["blocking"]
]
release_gate_required_ids = [
    check["id"] for check in release_gate_checks if check["required"]
]
release_gate_required_blocking_ids = [
    check["id"] for check in release_gate_checks
    if check["blocking"] and check["required"]
]
release_gate_optional_blocking_ids = [
    check["id"] for check in release_gate_checks
    if check["blocking"] and not check["required"]
]
release_gate_status_counts = {}
release_gate_blocker_groups = {}
release_gate_next_actions_by_check = {}
first_blocking_action = "none"
for check in release_gate_checks:
    status = check["status"]
    release_gate_status_counts[status] = release_gate_status_counts.get(status, 0) + 1
    if check["next_action"] != "none":
        release_gate_next_actions_by_check[check["id"]] = check["next_action"]
    if check["blocking"]:
        category = check["category"]
        release_gate_blocker_groups.setdefault(category, []).append(check["id"])
        if first_blocking_action == "none" and check["next_action"] != "none":
            first_blocking_action = check["next_action"]
release_gate_check_text = ", ".join(
    f"{check['id']}={check['status']}{'!' if check['blocking'] else ''}"
    for check in release_gate_checks
) or "none"
release_gate_blocking_text = ", ".join(release_gate_blocking_ids) or "none"
release_gate_blocker_group_text = ", ".join(
    f"{category}={','.join(ids)}"
    for category, ids in sorted(release_gate_blocker_groups.items())
) or "none"

compact_report = {
    "report_version": "funding_release_report_v0",
    "smoke_exit": smoke_exit,
    "report_exit_code": report_exit_code,
    "gate_status": gate_status,
    "release_gate_status": release_gate_status,
    "exit_reason": exit_reason,
    "contract": contract.get("funding_qa_contract_version", "unknown"),
    "release_gate_summary": {
        "status": release_gate_status,
        "total_checks": len(release_gate_checks),
        "required_checks": len(release_gate_required_ids),
        "blocking_checks": len(release_gate_blocking_ids),
        "blocking_ids": release_gate_blocking_ids,
        "required_ids": release_gate_required_ids,
        "required_blocking_ids": release_gate_required_blocking_ids,
        "optional_blocking_ids": release_gate_optional_blocking_ids,
        "blocker_groups": {
            key: release_gate_blocker_groups[key]
            for key in sorted(release_gate_blocker_groups)
        },
        "first_blocking_action": first_blocking_action,
        "next_actions_by_check": {
            key: release_gate_next_actions_by_check[key]
            for key in sorted(release_gate_next_actions_by_check)
        },
        "status_counts": {
            key: release_gate_status_counts[key]
            for key in sorted(release_gate_status_counts)
        },
    },
    "release_gate_checks": release_gate_checks,
    "run_context": {
        "report_profile": report_profile,
        "report_format": report_format,
        "report_output_file": requested_report_output_file or None,
        "report_output_enabled": bool(requested_report_output_file),
        "ci": ci_context,
        "base_url": payload.get("base_url") or requested_base_url,
        "frontend_url": payload.get("frontend_url") or requested_frontend_url,
        "compare_base_url": compare.get("compare_base_url") or requested_compare_base_url or None,
        "strict_mode": flag(strict_mode_raw),
        "fail_on_diff": flag(fail_on_diff_raw),
        "fail_on_release_not_ready": flag(fail_on_release_not_ready_raw),
        "report_require_ready": report_require_ready,
        "report_require_compare": report_require_compare,
        "run_frontend_check": flag(run_frontend_check_raw),
        "min_total_rows": min_total_rows,
    },
    "readiness_gate_status": readiness_gate_status,
    "readiness_status": readiness_status,
    "readiness_next_action": readiness_next_action,
    "readiness_checks": readiness_check_statuses,
    "data_quality_runway": data_quality_runway,
    "blocking_reasons": blocking_reasons,
    "next_actions": deduped_next_actions,
    "sources_with_rows": sources_with_rows,
    "funding_total_rows": contract.get("funding_total_rows", 0),
    "funding_rows_by_source": {
        key: source_rows[key] for key in sorted(source_rows)
    },
    "source_pair_statuses": {
        key: source_pair_statuses[key] for key in sorted(source_pair_statuses)
    },
    "frontend_checked": contract.get("frontend_checked", False),
    "missing_frontend_marker_count": len(missing_frontend),
    "missing_frontend_markers": missing_frontend,
    "compare_status": compare_status,
    "compare_gate_status": compare_gate_status,
    "compare_diff_count": diff_count,
    "compare_diff_fields": compare_diff_fields,
    "safety_status": safety_status,
    "unsafe_flags": unsafe_flags,
}

if requested_report_output_file:
    try:
        with open(requested_report_output_file, "w", encoding="utf-8") as output_handle:
            json.dump(compact_report, output_handle, ensure_ascii=False, indent=2)
            output_handle.write("\n")
    except OSError as exc:
        print(
            f"Funding release report output write failed: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(4)

if report_format == "json":
    print(json.dumps(compact_report, ensure_ascii=False, indent=2))
    raise SystemExit(report_exit_code)

print("Funding release report")
print(f"- report_version: {compact_report['report_version']}")
print(f"- smoke_exit: {compact_report['smoke_exit']}")
print(f"- report_exit_code: {compact_report['report_exit_code']}")
print(f"- gate_status: {compact_report['gate_status']}")
print(f"- release_gate_status: {compact_report['release_gate_status']}")
print(f"- exit_reason: {compact_report['exit_reason']}")
print(f"- contract: {compact_report['contract']}")
print(f"- release_gate_checks: {release_gate_check_text}")
print(f"- release_gate_blocking_ids: {release_gate_blocking_text}")
print(f"- release_gate_blocker_groups: {release_gate_blocker_group_text}")
print(f"- release_gate_first_blocking_action: {first_blocking_action}")
print(f"- base_url: {compact_report['run_context']['base_url']}")
print(f"- compare_base_url: {compact_report['run_context']['compare_base_url'] or 'none'}")
print(f"- report_profile: {compact_report['run_context']['report_profile']}")
print(f"- report_format: {compact_report['run_context']['report_format']}")
print(f"- report_output_file: {compact_report['run_context']['report_output_file'] or 'none'}")
print(f"- ci_provider: {compact_report['run_context']['ci']['provider']}")
print(f"- strict_mode: {compact_report['run_context']['strict_mode']}")
print(f"- report_require_ready: {compact_report['run_context']['report_require_ready']}")
print(f"- report_require_compare: {compact_report['run_context']['report_require_compare']}")
print(f"- readiness_gate_status: {compact_report['readiness_gate_status']}")
print(f"- readiness_status: {compact_report['readiness_status']}")
print(f"- readiness_next_action: {compact_report['readiness_next_action']}")
print(f"- readiness_checks: {readiness_check_text}")
print(f"- data_quality_runway_status: {runway_status}")
print(f"- data_quality_runway_blocking_gates: {', '.join(str(item) for item in runway_blocking_gate_ids) or 'none'}")
print(f"- blocking_reasons: {blocking_text}")
print(f"- next_actions: {next_action_text}")
print(f"- sources_with_rows: {sources_with_rows_text}")
print(f"- funding_total_rows: {compact_report['funding_total_rows']}")
print(f"- funding_rows_by_source: {source_row_text}")
print(f"- source_pair_statuses: {source_pair_text}")
print(f"- frontend_checked: {compact_report['frontend_checked']}")
print(f"- missing_frontend_markers: {compact_report['missing_frontend_marker_count']}")
print(f"- compare_status: {compact_report['compare_status']}")
print(f"- compare_gate_status: {compact_report['compare_gate_status']}")
print(f"- compare_diff_count: {diff_count_text}")
print(f"- compare_diff_fields: {compare_diff_text}")
print(f"- safety_status: {compact_report['safety_status']}")
if compact_report["unsafe_flags"]:
    print(f"- unsafe_flags: {', '.join(compact_report['unsafe_flags'])}")
raise SystemExit(report_exit_code)
PY
REPORT_EXIT=$?

if [ "$REPORT_EXIT" -ne 0 ]; then
  exit "$REPORT_EXIT"
fi

exit "$SMOKE_EXIT"
