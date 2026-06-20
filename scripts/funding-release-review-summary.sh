#!/usr/bin/env sh
set -eu

REVIEW_FILE="${1:-${FUNDING_RELEASE_REVIEW_SUMMARY_FILE:-artifacts/funding-release/funding-release-review.json}}"
SUMMARY_FORMAT="${FUNDING_RELEASE_REVIEW_SUMMARY_FORMAT:-markdown}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$SUMMARY_FORMAT" in
  markdown|text|json) ;;
  *)
    printf 'FUNDING_RELEASE_REVIEW_SUMMARY_FORMAT must be markdown, text or json.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release review summary.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$REVIEW_FILE" "$SUMMARY_FORMAT" <<'PY'
import json
import sys
from pathlib import Path

review_path = Path(sys.argv[1])
output_format = sys.argv[2]

allowed_statuses = {"passed", "blocked", "failed", "invalid_bundle", "incomplete", "unknown"}
errors = []

def add_error(message):
    errors.append(message)

def load_review(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Funding release review artifact not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Funding release review artifact is not valid JSON: {exc}")
    if not isinstance(value, dict):
        raise SystemExit("Funding release review artifact must be a JSON object")
    return value

def as_list(value):
    return value if isinstance(value, list) else []

def as_dict(value):
    return value if isinstance(value, dict) else {}

def short_sha(value):
    if not isinstance(value, str) or not value:
        return None
    return value[:12]

def text_value(value):
    if value is None or value == "":
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

def inline_code(value):
    value_text = text_value(value).replace("`", "'")
    return f"`{value_text}`"

def markdown_cell(value):
    return text_value(value).replace("|", "\\|").replace("\n", " ")

def file_row(name, entry):
    entry = as_dict(entry)
    return {
        "name": name,
        "configured": entry.get("configured") is True,
        "exists": entry.get("exists") is True,
        "json_valid": entry.get("json_valid"),
        "size_bytes": entry.get("size_bytes"),
        "sha256_short": short_sha(entry.get("sha256")),
    }

review = load_review(review_path)
review_version = review.get("review_version")
if review_version != "funding_release_bundle_review_v0":
    add_error("review_version must be funding_release_bundle_review_v0")

review_status = review.get("review_status")
if review_status not in allowed_statuses:
    add_error(f"review_status has unsupported value {review_status!r}")

recommended_next_action = review.get("recommended_next_action") or "Inspect Funding release review artifact"
required_blocking_ids = as_list(review.get("required_blocking_ids"))
optional_blocking_ids = as_list(review.get("optional_blocking_ids"))
files = as_dict(review.get("files"))
run_context = as_dict(review.get("run_context"))
file_rows = [
    file_row("report", files.get("report")),
    file_row("stdout", files.get("stdout")),
    file_row("validation", files.get("validation")),
    file_row("manifest", files.get("manifest")),
]

if review_status == "passed":
    runbook_status = "ready_for_release_evidence"
elif review_status == "blocked":
    runbook_status = "release_blocked"
elif review_status == "failed":
    runbook_status = "smoke_failed"
elif review_status == "invalid_bundle":
    runbook_status = "bundle_integrity_failed"
elif review_status == "incomplete":
    runbook_status = "bundle_review_incomplete"
else:
    runbook_status = "needs_manual_inspection"

summary = {
    "summary_version": "funding_release_review_summary_v0",
    "artifact": str(review_path),
    "summary_status": "failed" if errors else "passed",
    "runbook_status": runbook_status,
    "review_status": review_status,
    "recommended_next_action": recommended_next_action,
    "bundle_exit_code": review.get("bundle_exit_code"),
    "report_exit_code": review.get("report_exit_code"),
    "validation_exit_code": review.get("validation_exit_code"),
    "bundle_validation_status": review.get("bundle_validation_status"),
    "validation_status": review.get("validation_status"),
    "release_gate_status": review.get("release_gate_status"),
    "exit_reason": review.get("exit_reason"),
    "readiness_gate_status": review.get("readiness_gate_status"),
    "compare_gate_status": review.get("compare_gate_status"),
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "first_blocking_action": review.get("first_blocking_action"),
    "first_optional_action": review.get("first_optional_action"),
    "run_context": {
        "report_profile": run_context.get("report_profile"),
        "ci_provider": run_context.get("ci_provider"),
        "base_url": run_context.get("base_url"),
        "frontend_url": run_context.get("frontend_url"),
        "compare_base_url": run_context.get("compare_base_url"),
        "run_frontend_check": run_context.get("run_frontend_check"),
        "min_total_rows": run_context.get("min_total_rows"),
    },
    "files": file_rows,
    "errors": errors,
}

if output_format == "json":
    print(json.dumps(summary, ensure_ascii=False, indent=2))
elif output_format == "text":
    print("Funding release review summary")
    print(f"- artifact: {review_path}")
    print(f"- runbook_status: {runbook_status}")
    print(f"- review_status: {review_status}")
    print(f"- recommended_next_action: {recommended_next_action}")
    print(f"- bundle_exit_code: {text_value(review.get('bundle_exit_code'))}")
    print(f"- report_exit_code: {text_value(review.get('report_exit_code'))}")
    print(f"- validation_exit_code: {text_value(review.get('validation_exit_code'))}")
    print(f"- bundle_validation_status: {text_value(review.get('bundle_validation_status'))}")
    print(f"- release_gate_status: {text_value(review.get('release_gate_status'))}")
    print(f"- exit_reason: {text_value(review.get('exit_reason'))}")
    print(f"- readiness_gate_status: {text_value(review.get('readiness_gate_status'))}")
    print(f"- compare_gate_status: {text_value(review.get('compare_gate_status'))}")
    print(f"- required_blocking_ids: {', '.join(required_blocking_ids) if required_blocking_ids else 'none'}")
    print(f"- optional_blocking_ids: {', '.join(optional_blocking_ids) if optional_blocking_ids else 'none'}")
    for row in file_rows:
        print(
            "- file:"
            f" {row['name']}"
            f" configured={text_value(row['configured'])}"
            f" exists={text_value(row['exists'])}"
            f" json_valid={text_value(row['json_valid'])}"
            f" size_bytes={text_value(row['size_bytes'])}"
            f" sha256={text_value(row['sha256_short'])}"
        )
else:
    print("### Funding Release Review")
    print("")
    print(f"- runbook_status: {inline_code(runbook_status)}")
    print(f"- review_status: {inline_code(review_status)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print(f"- bundle_exit_code: {inline_code(review.get('bundle_exit_code'))}")
    print(f"- report_exit_code: {inline_code(review.get('report_exit_code'))}")
    print(f"- validation_exit_code: {inline_code(review.get('validation_exit_code'))}")
    print(f"- bundle_validation_status: {inline_code(review.get('bundle_validation_status'))}")
    print(f"- validation_status: {inline_code(review.get('validation_status'))}")
    print(f"- release_gate_status: {inline_code(review.get('release_gate_status'))}")
    print(f"- exit_reason: {inline_code(review.get('exit_reason'))}")
    print(f"- readiness_gate_status: {inline_code(review.get('readiness_gate_status'))}")
    print(f"- compare_gate_status: {inline_code(review.get('compare_gate_status'))}")
    print("")
    print("#### Required Blockers")
    if required_blocking_ids:
        for blocker_id in required_blocking_ids:
            print(f"- {inline_code(blocker_id)}")
    else:
        print("- none")
    print("")
    print("#### Optional Blockers")
    if optional_blocking_ids:
        for blocker_id in optional_blocking_ids:
            print(f"- {inline_code(blocker_id)}")
    else:
        print("- none")
    print("")
    print("#### First Actions")
    print(f"- required: {inline_code(review.get('first_blocking_action'))}")
    print(f"- optional: {inline_code(review.get('first_optional_action'))}")
    print("")
    print("#### Run Context")
    print(f"- report_profile: {inline_code(run_context.get('report_profile'))}")
    print(f"- ci_provider: {inline_code(run_context.get('ci_provider'))}")
    print(f"- base_url: {inline_code(run_context.get('base_url'))}")
    print(f"- frontend_url: {inline_code(run_context.get('frontend_url'))}")
    print(f"- compare_base_url: {inline_code(run_context.get('compare_base_url'))}")
    print(f"- run_frontend_check: {inline_code(run_context.get('run_frontend_check'))}")
    print(f"- min_total_rows: {inline_code(run_context.get('min_total_rows'))}")
    print("")
    print("#### File Integrity")
    print("| File | Configured | Exists | JSON | Size | SHA-256 |")
    print("|---|---:|---:|---:|---:|---|")
    for row in file_rows:
        print(
            f"| {markdown_cell(row['name'])} "
            f"| {markdown_cell(row['configured'])} "
            f"| {markdown_cell(row['exists'])} "
            f"| {markdown_cell(row['json_valid'])} "
            f"| {markdown_cell(row['size_bytes'])} "
            f"| {markdown_cell(row['sha256_short'])} |"
        )
    if errors:
        print("")
        print("#### Summary Errors")
        for error in errors:
            print(f"- {inline_code(error)}")

if errors:
    raise SystemExit(1)
PY
