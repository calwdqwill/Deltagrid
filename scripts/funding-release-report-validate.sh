#!/usr/bin/env sh
set -eu

REPORT_FILE="${1:-${FUNDING_RELEASE_REPORT_VALIDATE_FILE:-${FUNDING_RELEASE_REPORT_OUTPUT:-artifacts/funding-release/funding-release-report.json}}}"
VALIDATE_FORMAT="${FUNDING_RELEASE_REPORT_VALIDATE_FORMAT:-text}"
VALIDATE_REQUIRE_PASSED="${FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_PASSED:-0}"
VALIDATE_REQUIRE_CI_CONTEXT="${FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_CI_CONTEXT:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

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

case "$VALIDATE_FORMAT" in
  text|json) ;;
  *)
    printf 'FUNDING_RELEASE_REPORT_VALIDATE_FORMAT must be text or json.\n' >&2
    exit 1
    ;;
esac

require_bool "FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_PASSED" "$VALIDATE_REQUIRE_PASSED"
require_bool "FUNDING_RELEASE_REPORT_VALIDATE_REQUIRE_CI_CONTEXT" "$VALIDATE_REQUIRE_CI_CONTEXT"

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release report validation.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$REPORT_FILE" "$VALIDATE_FORMAT" "$VALIDATE_REQUIRE_PASSED" "$VALIDATE_REQUIRE_CI_CONTEXT" <<'PY'
import json
import sys
from pathlib import Path

report_path, output_format, require_passed_raw, require_ci_context_raw = sys.argv[1:5]
require_passed = require_passed_raw == "1"
require_ci_context = require_ci_context_raw == "1"

errors = []
warnings = []

def add_error(message):
    errors.append(message)

def is_dict(value):
    return isinstance(value, dict)

def is_list(value):
    return isinstance(value, list)

def require_dict(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, dict):
        add_error(f"{path}.{key} must be object")
        return {}
    return value

def require_list(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, list):
        add_error(f"{path}.{key} must be array")
        return []
    return value

def require_int(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, int):
        add_error(f"{path}.{key} must be integer")
        return None
    return value

def require_str(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, str):
        add_error(f"{path}.{key} must be string")
        return ""
    return value

def require_enum(parent, key, allowed, path):
    value = require_str(parent, key, path)
    if value and value not in allowed:
        add_error(f"{path}.{key} has unsupported value {value!r}")
    return value

def require_bool_value(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, bool):
        add_error(f"{path}.{key} must be boolean")
        return None
    return value

try:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
except FileNotFoundError:
    raise SystemExit(f"Funding release report artifact not found: {report_path}")
except json.JSONDecodeError as exc:
    raise SystemExit(f"Funding release report artifact is not valid JSON: {exc}")

if not isinstance(report, dict):
    raise SystemExit("Funding release report artifact must be a JSON object")

required_top_fields = [
    "report_version",
    "smoke_exit",
    "report_exit_code",
    "gate_status",
    "release_gate_status",
    "exit_reason",
    "contract",
    "release_gate_summary",
    "release_gate_checks",
    "run_context",
    "readiness_gate_status",
    "readiness_status",
    "readiness_checks",
    "blocking_reasons",
    "next_actions",
    "funding_total_rows",
    "funding_rows_by_source",
    "source_pair_statuses",
    "compare_status",
    "compare_gate_status",
    "safety_status",
    "unsafe_flags",
]
for field in required_top_fields:
    if field not in report:
        add_error(f"missing top-level field: {field}")

report_version = require_str(report, "report_version", "report")
if report_version != "funding_release_report_v0":
    add_error("report.report_version must be funding_release_report_v0")

smoke_exit = require_int(report, "smoke_exit", "report")
report_exit_code = require_int(report, "report_exit_code", "report")
gate_status = require_enum(report, "gate_status", {"passed", "failed"}, "report")
release_gate_status = require_enum(report, "release_gate_status", {"passed", "blocked", "failed"}, "report")
exit_reason = require_enum(
    report,
    "exit_reason",
    {"passed", "smoke_failed", "readiness_not_ready", "compare_not_aligned"},
    "report",
)
require_enum(report, "readiness_gate_status", {"ready", "not_ready"}, "report")
require_str(report, "readiness_status", "report")
compare_status = require_str(report, "compare_status", "report")
compare_gate_status = require_str(report, "compare_gate_status", "report")
safety_status = require_enum(report, "safety_status", {"locked", "unsafe"}, "report")
unsafe_flags = require_list(report, "unsafe_flags", "report")
release_gate_summary = require_dict(report, "release_gate_summary", "report")
release_gate_checks = require_list(report, "release_gate_checks", "report")
run_context = require_dict(report, "run_context", "report")
readiness_checks = require_dict(report, "readiness_checks", "report")
require_list(report, "blocking_reasons", "report")
require_list(report, "next_actions", "report")
require_int(report, "funding_total_rows", "report")
require_dict(report, "funding_rows_by_source", "report")
require_dict(report, "source_pair_statuses", "report")
require_list(report, "compare_diff_fields", "report")

if smoke_exit is not None and gate_status:
    expected_gate_status = "passed" if smoke_exit == 0 else "failed"
    if gate_status != expected_gate_status:
        add_error("report.gate_status must match smoke_exit")

if report_exit_code is not None and exit_reason:
    if report_exit_code == 0 and exit_reason != "passed":
        add_error("exit_reason must be passed when report_exit_code is 0")
    if report_exit_code != 0 and exit_reason == "passed":
        add_error("exit_reason must not be passed when report_exit_code is non-zero")

if exit_reason == "smoke_failed" and release_gate_status != "failed":
    add_error("release_gate_status must be failed when exit_reason is smoke_failed")
if exit_reason in {"readiness_not_ready", "compare_not_aligned"} and release_gate_status != "blocked":
    add_error("release_gate_status must be blocked for report-level gate failures")
if exit_reason == "passed" and release_gate_status != "passed":
    add_error("release_gate_status must be passed when exit_reason is passed")
if require_passed and release_gate_status != "passed":
    add_error("release_gate_status must be passed because validation requires a passed report")

if safety_status == "locked" and unsafe_flags:
    add_error("unsafe_flags must be empty when safety_status is locked")
if safety_status == "unsafe" and not unsafe_flags:
    add_error("unsafe_flags must be non-empty when safety_status is unsafe")

summary_status = release_gate_summary.get("status")
if summary_status != release_gate_status:
    add_error("release_gate_summary.status must match release_gate_status")

summary_total = release_gate_summary.get("total_checks")
if summary_total != len(release_gate_checks):
    add_error("release_gate_summary.total_checks must match release_gate_checks length")

summary_required = release_gate_summary.get("required_checks")
summary_blocking = release_gate_summary.get("blocking_checks")
summary_required_ids = release_gate_summary.get("required_ids")
summary_blocking_ids = release_gate_summary.get("blocking_ids")
summary_required_blocking_ids = release_gate_summary.get("required_blocking_ids")
summary_optional_blocking_ids = release_gate_summary.get("optional_blocking_ids")
summary_blocker_groups = release_gate_summary.get("blocker_groups")
summary_next_actions_by_check = release_gate_summary.get("next_actions_by_check")
summary_status_counts = release_gate_summary.get("status_counts")

for key, value in [
    ("required_ids", summary_required_ids),
    ("blocking_ids", summary_blocking_ids),
    ("required_blocking_ids", summary_required_blocking_ids),
    ("optional_blocking_ids", summary_optional_blocking_ids),
]:
    if not isinstance(value, list):
        add_error(f"release_gate_summary.{key} must be array")
if not isinstance(summary_blocker_groups, dict):
    add_error("release_gate_summary.blocker_groups must be object")
    summary_blocker_groups = {}
if not isinstance(summary_next_actions_by_check, dict):
    add_error("release_gate_summary.next_actions_by_check must be object")
    summary_next_actions_by_check = {}
if not isinstance(summary_status_counts, dict):
    add_error("release_gate_summary.status_counts must be object")
    summary_status_counts = {}

valid_check_categories = {
    "smoke",
    "readiness",
    "compare",
    "data",
    "frontend",
    "safety",
    "run_context",
    "general",
}
check_ids = []
required_ids = []
blocking_ids = []
required_blocking_ids = []
optional_blocking_ids = []
status_counts = {}
blocker_groups = {}
next_actions_by_check = {}
for index, check in enumerate(release_gate_checks):
    path = f"release_gate_checks[{index}]"
    if not isinstance(check, dict):
        add_error(f"{path} must be object")
        continue
    check_id = require_str(check, "id", path)
    category = require_str(check, "category", path)
    status = require_str(check, "status", path)
    required = require_bool_value(check, "required", path)
    blocking = require_bool_value(check, "blocking", path)
    next_action = require_str(check, "next_action", path)
    if category and category not in valid_check_categories:
        add_error(f"{path}.category has unsupported value {category!r}")
    if check_id:
        if check_id in check_ids:
            add_error(f"duplicate release gate check id: {check_id}")
        check_ids.append(check_id)
    if status:
        status_counts[status] = status_counts.get(status, 0) + 1
    if required:
        required_ids.append(check_id)
    if blocking:
        blocking_ids.append(check_id)
        if category:
            blocker_groups.setdefault(category, []).append(check_id)
        if required:
            required_blocking_ids.append(check_id)
        else:
            optional_blocking_ids.append(check_id)
    if next_action and next_action != "none" and check_id:
        next_actions_by_check[check_id] = next_action

if isinstance(summary_required, int) and summary_required != len(required_ids):
    add_error("release_gate_summary.required_checks must match required release_gate_checks")
if isinstance(summary_blocking, int) and summary_blocking != len(blocking_ids):
    add_error("release_gate_summary.blocking_checks must match blocking release_gate_checks")
if isinstance(summary_required_ids, list) and summary_required_ids != required_ids:
    add_error("release_gate_summary.required_ids must match release_gate_checks order")
if isinstance(summary_blocking_ids, list) and summary_blocking_ids != blocking_ids:
    add_error("release_gate_summary.blocking_ids must match release_gate_checks order")
if isinstance(summary_required_blocking_ids, list) and summary_required_blocking_ids != required_blocking_ids:
    add_error("release_gate_summary.required_blocking_ids must match release_gate_checks")
if isinstance(summary_optional_blocking_ids, list) and summary_optional_blocking_ids != optional_blocking_ids:
    add_error("release_gate_summary.optional_blocking_ids must match release_gate_checks")
if summary_blocker_groups != {key: blocker_groups[key] for key in sorted(blocker_groups)}:
    add_error("release_gate_summary.blocker_groups must match blocking checks")
if summary_next_actions_by_check != {key: next_actions_by_check[key] for key in sorted(next_actions_by_check)}:
    add_error("release_gate_summary.next_actions_by_check must match release_gate_checks")
if summary_status_counts != {key: status_counts[key] for key in sorted(status_counts)}:
    add_error("release_gate_summary.status_counts must match release_gate_checks")

run_context_required_fields = [
    "report_profile",
    "report_format",
    "report_output_enabled",
    "ci",
    "base_url",
    "frontend_url",
    "strict_mode",
    "fail_on_diff",
    "fail_on_release_not_ready",
    "report_require_ready",
    "report_require_compare",
    "run_frontend_check",
    "min_total_rows",
]
for field in run_context_required_fields:
    if field not in run_context:
        add_error(f"run_context missing field: {field}")

require_enum(run_context, "report_profile", {"manual", "ci"}, "run_context")
require_enum(run_context, "report_format", {"text", "json"}, "run_context")
for bool_field in [
    "report_output_enabled",
    "strict_mode",
    "fail_on_diff",
    "fail_on_release_not_ready",
    "report_require_ready",
    "report_require_compare",
    "run_frontend_check",
]:
    require_bool_value(run_context, bool_field, "run_context")
ci_context = require_dict(run_context, "ci", "run_context")
ci_provider = require_enum(ci_context, "provider", {"local", "generic_ci", "github_actions"}, "run_context.ci")
ci_is_ci = require_bool_value(ci_context, "is_ci", "run_context.ci")
if ci_provider == "local" and ci_is_ci is True:
    add_error("run_context.ci.is_ci must be false for local provider")
if ci_provider in {"generic_ci", "github_actions"} and ci_is_ci is False:
    add_error("run_context.ci.is_ci must be true for CI providers")
if require_ci_context and ci_provider == "local":
    add_error("run_context.ci.provider must not be local when CI context is required")
if ci_provider == "github_actions":
    github_context = require_dict(ci_context, "github", "run_context.ci")
    if not github_context.get("run_id"):
        warnings.append("run_context.ci.github.run_id is empty")

expected_readiness_checks = {
    "data_health",
    "funding_rows",
    "source_coverage",
    "frontend_markers",
    "safety_boundary",
}
missing_readiness_checks = sorted(expected_readiness_checks - set(readiness_checks))
if missing_readiness_checks:
    add_error(f"readiness_checks missing required keys: {', '.join(missing_readiness_checks)}")

if compare_gate_status == "aligned" and compare_status != "aligned":
    add_error("compare_gate_status aligned requires compare_status aligned")

result = {
    "status": "failed" if errors else "passed",
    "artifact": report_path,
    "release_gate_status": release_gate_status,
    "report_exit_code": report_exit_code,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print("Funding release report validation")
    print(f"- artifact: {report_path}")
    print(f"- status: {result['status']}")
    print(f"- release_gate_status: {release_gate_status}")
    print(f"- report_exit_code: {report_exit_code}")
    print(f"- errors: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
    if warnings:
        print(f"- warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")

if errors:
    raise SystemExit(1)
PY
