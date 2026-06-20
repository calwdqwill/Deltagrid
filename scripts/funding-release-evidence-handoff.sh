#!/usr/bin/env sh
set -eu

REVIEW_FILE="${1:-${FUNDING_RELEASE_HANDOFF_REVIEW_FILE:-artifacts/funding-release/funding-release-review.json}}"
HANDOFF_FORMAT="${FUNDING_RELEASE_HANDOFF_FORMAT:-markdown}"
SUMMARY_FILE="${FUNDING_RELEASE_HANDOFF_SUMMARY_FILE:-}"
MANIFEST_FILE="${FUNDING_RELEASE_HANDOFF_MANIFEST_FILE:-}"
BUNDLE_VALIDATION_FILE="${FUNDING_RELEASE_HANDOFF_BUNDLE_VALIDATION_FILE:-}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$HANDOFF_FORMAT" in
  markdown|text|json) ;;
  *)
    printf 'FUNDING_RELEASE_HANDOFF_FORMAT must be markdown, text or json.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence handoff.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$REVIEW_FILE" "$HANDOFF_FORMAT" "$SUMMARY_FILE" "$MANIFEST_FILE" "$BUNDLE_VALIDATION_FILE" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

review_path = Path(sys.argv[1])
output_format = sys.argv[2]
summary_path_raw = sys.argv[3]
manifest_path_raw = sys.argv[4]
bundle_validation_path_raw = sys.argv[5]

allowed_review_statuses = {"passed", "blocked", "failed", "invalid_bundle", "incomplete", "unknown"}
errors = []
warnings = []

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

def default_path(raw_value, filename):
    if raw_value:
        return Path(raw_value)
    return review_path.parent / filename

def read_required_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Funding release review artifact not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Funding release review artifact is not valid JSON: {exc}")
    if not isinstance(value, dict):
        raise SystemExit("Funding release review artifact must be a JSON object")
    return value

def read_optional_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"status": "missing", "artifact": str(path)}
    except json.JSONDecodeError:
        return {"status": "parse_error", "artifact": str(path)}
    return value if isinstance(value, dict) else {"status": "invalid_shape", "artifact": str(path)}

def as_dict(value):
    return value if isinstance(value, dict) else {}

def as_list(value):
    return value if isinstance(value, list) else []

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

def short_sha(value):
    if not isinstance(value, str) or not value:
        return None
    return value[:12]

def actual_file_row(name, path, required):
    exists = path.is_file()
    size_bytes = None
    sha256_short = None
    json_valid = None
    if exists:
        data = path.read_bytes()
        size_bytes = len(data)
        sha256_short = hashlib.sha256(data).hexdigest()[:12]
        try:
            json.loads(data.decode("utf-8"))
            json_valid = True
        except Exception:
            json_valid = False
    return {
        "name": name,
        "path": str(path),
        "required": required,
        "configured": True,
        "exists": exists,
        "json_valid": json_valid,
        "size_bytes": size_bytes,
        "sha256_short": sha256_short,
    }

def review_file_row(name, entry, required):
    entry = as_dict(entry)
    return {
        "name": name,
        "path": entry.get("path"),
        "required": required,
        "configured": entry.get("configured") is True,
        "exists": entry.get("exists") is True,
        "json_valid": entry.get("json_valid"),
        "size_bytes": entry.get("size_bytes"),
        "sha256_short": short_sha(entry.get("sha256")),
    }

review = read_required_json(review_path)
summary_path = default_path(summary_path_raw, "funding-release-summary.md")
manifest_path = default_path(manifest_path_raw, "funding-release-manifest.json")
bundle_validation_path = default_path(bundle_validation_path_raw, "funding-release-bundle-validation.json")
manifest = read_optional_json(manifest_path)
bundle_validation = read_optional_json(bundle_validation_path)

if review.get("review_version") != "funding_release_bundle_review_v0":
    add_error("review_version must be funding_release_bundle_review_v0")

review_status = review.get("review_status")
if review_status not in allowed_review_statuses:
    add_error(f"review_status has unsupported value {review_status!r}")

bundle_validation_status = review.get("bundle_validation_status")
if isinstance(bundle_validation, dict) and bundle_validation.get("status") in {"passed", "failed"}:
    if bundle_validation_status != bundle_validation.get("status"):
        add_warning("review.bundle_validation_status differs from bundle validation artifact status")

release_gate_status = review.get("release_gate_status")
validation_status = review.get("validation_status")
required_blocking_ids = as_list(review.get("required_blocking_ids"))
optional_blocking_ids = as_list(review.get("optional_blocking_ids"))
files = as_dict(review.get("files"))
run_context = as_dict(review.get("run_context"))

if review_status == "passed" and bundle_validation_status == "passed":
    evidence_status = "ready_to_attach"
elif review_status == "blocked" and bundle_validation_status == "passed":
    evidence_status = "blocked_with_valid_evidence"
elif review_status == "failed" and bundle_validation_status == "passed":
    evidence_status = "smoke_failed_with_valid_evidence"
elif review_status == "invalid_bundle":
    evidence_status = "bundle_integrity_failed"
elif review_status == "incomplete":
    evidence_status = "bundle_review_incomplete"
else:
    evidence_status = "manual_inspection_required"

release_evidence_ready = evidence_status == "ready_to_attach"
debug_evidence_ready = evidence_status in {"blocked_with_valid_evidence", "smoke_failed_with_valid_evidence"}

artifact_rows = [
    review_file_row("report", files.get("report"), True),
    review_file_row("stdout", files.get("stdout"), False),
    review_file_row("validation", files.get("validation"), True),
    actual_file_row("manifest", manifest_path, True),
    actual_file_row("bundle_validation", bundle_validation_path, True),
    actual_file_row("review", review_path, True),
    actual_file_row("summary", summary_path, True),
]
missing_required = [row["name"] for row in artifact_rows if row["required"] and not row["exists"]]
if missing_required:
    add_warning("missing required handoff artifacts: " + ", ".join(missing_required))

handoff_status = "failed" if errors else ("incomplete" if missing_required else "passed")
recommended_next_action = review.get("recommended_next_action") or "Inspect Funding release review artifact"

local_commands = [
    f"sh scripts/funding-release-report-validate.sh {manifest_path.parent / 'funding-release-report.json'}",
    f"sh scripts/funding-release-bundle-validate.sh {manifest_path}",
    f"sh scripts/funding-release-bundle-review.sh {manifest_path}",
    f"sh scripts/funding-release-review-summary.sh {review_path}",
    f"sh scripts/funding-release-evidence-handoff.sh {review_path}",
]

handoff = {
    "handoff_version": "funding_release_evidence_handoff_v0",
    "artifact": str(review_path),
    "handoff_status": handoff_status,
    "evidence_status": evidence_status,
    "release_evidence_ready": release_evidence_ready,
    "debug_evidence_ready": debug_evidence_ready,
    "review_status": review_status,
    "recommended_next_action": recommended_next_action,
    "bundle_exit_code": review.get("bundle_exit_code"),
    "report_exit_code": review.get("report_exit_code"),
    "validation_exit_code": review.get("validation_exit_code"),
    "bundle_validation_status": bundle_validation_status,
    "validation_status": validation_status,
    "release_gate_status": release_gate_status,
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
    "artifacts": artifact_rows,
    "local_commands": local_commands,
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(handoff, ensure_ascii=False, indent=2))
elif output_format == "text":
    print("Funding release evidence handoff")
    print(f"- artifact: {review_path}")
    print(f"- handoff_status: {handoff_status}")
    print(f"- evidence_status: {evidence_status}")
    print(f"- release_evidence_ready: {text_value(release_evidence_ready)}")
    print(f"- debug_evidence_ready: {text_value(debug_evidence_ready)}")
    print(f"- review_status: {text_value(review_status)}")
    print(f"- recommended_next_action: {recommended_next_action}")
    print(f"- release_gate_status: {text_value(release_gate_status)}")
    print(f"- exit_reason: {text_value(review.get('exit_reason'))}")
    print(f"- required_blocking_ids: {', '.join(required_blocking_ids) if required_blocking_ids else 'none'}")
    print(f"- optional_blocking_ids: {', '.join(optional_blocking_ids) if optional_blocking_ids else 'none'}")
    for row in artifact_rows:
        print(
            "- artifact_file:"
            f" {row['name']}"
            f" required={text_value(row['required'])}"
            f" exists={text_value(row['exists'])}"
            f" size_bytes={text_value(row['size_bytes'])}"
        )
    if warnings:
        print(f"- warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
else:
    print("### Funding Release Evidence Handoff")
    print("")
    print(f"- handoff_status: {inline_code(handoff_status)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- release_evidence_ready: {inline_code(release_evidence_ready)}")
    print(f"- debug_evidence_ready: {inline_code(debug_evidence_ready)}")
    print(f"- review_status: {inline_code(review_status)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Release State")
    print(f"- bundle_exit_code: {inline_code(review.get('bundle_exit_code'))}")
    print(f"- report_exit_code: {inline_code(review.get('report_exit_code'))}")
    print(f"- validation_exit_code: {inline_code(review.get('validation_exit_code'))}")
    print(f"- bundle_validation_status: {inline_code(bundle_validation_status)}")
    print(f"- validation_status: {inline_code(validation_status)}")
    print(f"- release_gate_status: {inline_code(release_gate_status)}")
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
    print("#### Artifact Checklist")
    print("| Artifact | Required | Exists | JSON | Size | SHA-256 |")
    print("|---|---:|---:|---:|---:|---|")
    for row in artifact_rows:
        print(
            f"| {markdown_cell(row['name'])} "
            f"| {markdown_cell(row['required'])} "
            f"| {markdown_cell(row['exists'])} "
            f"| {markdown_cell(row['json_valid'])} "
            f"| {markdown_cell(row['size_bytes'])} "
            f"| {markdown_cell(row['sha256_short'])} |"
        )
    print("")
    print("#### Local Follow-up Commands")
    for command in local_commands:
        print(f"- `{command}`")
    if warnings:
        print("")
        print("#### Handoff Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")
    if errors:
        print("")
        print("#### Handoff Errors")
        for error in errors:
            print(f"- {inline_code(error)}")

if errors:
    raise SystemExit(1)
PY
