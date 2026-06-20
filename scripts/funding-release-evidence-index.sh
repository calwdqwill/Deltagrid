#!/usr/bin/env sh
set -eu

BUNDLE_DIR="${1:-${FUNDING_RELEASE_INDEX_DIR:-artifacts/funding-release}}"
INDEX_FORMAT="${FUNDING_RELEASE_INDEX_FORMAT:-markdown}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$INDEX_FORMAT" in
  markdown|text|json) ;;
  *)
    printf 'FUNDING_RELEASE_INDEX_FORMAT must be markdown, text or json.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence index.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BUNDLE_DIR" "$INDEX_FORMAT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle_dir = Path(sys.argv[1])
output_format = sys.argv[2]
errors = []
warnings = []

expected_artifacts = [
    {
        "id": "report",
        "filename": "funding-release-report.json",
        "required": True,
        "json": True,
        "open_order": 4,
        "purpose": "Compact release report",
    },
    {
        "id": "stdout",
        "filename": "funding-release-report.stdout.json",
        "required": False,
        "json": True,
        "open_order": 10,
        "purpose": "Optional raw report stdout",
    },
    {
        "id": "validation",
        "filename": "funding-release-validation.json",
        "required": True,
        "json": True,
        "open_order": 7,
        "purpose": "Compact report validation result",
    },
    {
        "id": "manifest",
        "filename": "funding-release-manifest.json",
        "required": True,
        "json": True,
        "open_order": 6,
        "purpose": "Evidence bundle manifest",
    },
    {
        "id": "bundle_validation",
        "filename": "funding-release-bundle-validation.json",
        "required": True,
        "json": True,
        "open_order": 8,
        "purpose": "Manifest/checksum validation",
    },
    {
        "id": "review",
        "filename": "funding-release-review.json",
        "required": True,
        "json": True,
        "open_order": 5,
        "purpose": "Runbook review JSON",
    },
    {
        "id": "summary",
        "filename": "funding-release-summary.md",
        "required": True,
        "json": False,
        "open_order": 2,
        "purpose": "GitHub/release summary",
    },
    {
        "id": "handoff",
        "filename": "funding-release-handoff.md",
        "required": True,
        "json": False,
        "open_order": 3,
        "purpose": "Release handoff checklist",
    },
    {
        "id": "audit",
        "filename": "funding-release-audit.json",
        "required": True,
        "json": True,
        "open_order": 9,
        "purpose": "Machine-readable bundle audit",
    },
    {
        "id": "audit_markdown",
        "filename": "funding-release-audit.md",
        "required": True,
        "json": False,
        "open_order": 1,
        "purpose": "Human-readable bundle audit",
    },
]

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

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

def read_file_info(spec):
    path = bundle_dir / spec["filename"]
    info = {
        "id": spec["id"],
        "filename": spec["filename"],
        "path": str(path),
        "required": spec["required"],
        "json_expected": spec["json"],
        "open_order": spec["open_order"],
        "purpose": spec["purpose"],
        "exists": path.is_file(),
        "size_bytes": None,
        "sha256": None,
        "sha256_short": None,
        "json_valid": None,
    }
    parsed = None
    if not path.is_file():
        if spec["required"]:
            add_error(f"missing required artifact: {spec['filename']}")
        return info, parsed

    data = path.read_bytes()
    info["size_bytes"] = len(data)
    info["sha256"] = hashlib.sha256(data).hexdigest()
    info["sha256_short"] = info["sha256"][:12]
    if spec["json"]:
        try:
            value = json.loads(data.decode("utf-8"))
            info["json_valid"] = isinstance(value, dict)
            if isinstance(value, dict):
                parsed = value
            else:
                add_error(f"{spec['filename']} must be a JSON object")
        except Exception as exc:
            info["json_valid"] = False
            add_error(f"{spec['filename']} is not valid JSON: {exc}")
    return info, parsed

if not bundle_dir.exists():
    raise SystemExit(f"Funding release evidence bundle directory not found: {bundle_dir}")
if not bundle_dir.is_dir():
    raise SystemExit(f"Funding release evidence bundle path is not a directory: {bundle_dir}")

artifacts = []
parsed = {}
for spec in expected_artifacts:
    row, value = read_file_info(spec)
    artifacts.append(row)
    if value is not None:
        parsed[spec["id"]] = value

report = as_dict(parsed.get("report"))
validation = as_dict(parsed.get("validation"))
manifest = as_dict(parsed.get("manifest"))
bundle_validation = as_dict(parsed.get("bundle_validation"))
review = as_dict(parsed.get("review"))
audit = as_dict(parsed.get("audit"))

if report and report.get("report_version") != "funding_release_report_v0":
    add_error("report_version must be funding_release_report_v0")
if validation and validation.get("status") not in {"passed", "failed"}:
    add_error("validation.status must be passed or failed")
if manifest and manifest.get("manifest_version") != "funding_release_ci_bundle_v0":
    add_error("manifest_version must be funding_release_ci_bundle_v0")
if bundle_validation and bundle_validation.get("status") not in {"passed", "failed"}:
    add_error("bundle_validation.status must be passed or failed")
if review and review.get("review_version") != "funding_release_bundle_review_v0":
    add_error("review_version must be funding_release_bundle_review_v0")
if audit and audit.get("audit_version") != "funding_release_evidence_audit_v0":
    add_error("audit_version must be funding_release_evidence_audit_v0")

if audit and audit.get("audit_status") != "passed":
    add_error("audit_status must be passed for an attachable evidence bundle")
if bundle_validation and bundle_validation.get("status") != "passed":
    add_error("bundle_validation.status must be passed for an attachable evidence bundle")

review_status = review.get("review_status") if review else None
audit_status = audit.get("audit_status") if audit else None
evidence_status = audit.get("evidence_status") if audit else None
release_gate_status = review.get("release_gate_status") or report.get("release_gate_status")
recommended_next_action = review.get("recommended_next_action") or audit.get("recommended_next_action") or "Inspect Funding release evidence bundle"
required_blocking_ids = as_list(review.get("required_blocking_ids")) or as_list(audit.get("required_blocking_ids"))
optional_blocking_ids = as_list(review.get("optional_blocking_ids")) or as_list(audit.get("optional_blocking_ids"))
ready_for_release_notes = audit.get("ready_for_release_notes") if audit else review_status == "passed"
ready_for_debug_review = audit.get("ready_for_debug_review") if audit else review_status in {"blocked", "failed"}

open_order = sorted(artifacts, key=lambda row: (row["open_order"], row["filename"]))
review_commands = [
    f"sh scripts/funding-release-evidence-audit.sh {bundle_dir}",
    f"sh scripts/funding-release-evidence-handoff.sh {bundle_dir / 'funding-release-review.json'}",
    f"sh scripts/funding-release-review-summary.sh {bundle_dir / 'funding-release-review.json'}",
    f"sh scripts/funding-release-bundle-review.sh {bundle_dir / 'funding-release-manifest.json'}",
    f"sh scripts/funding-release-bundle-validate.sh {bundle_dir / 'funding-release-manifest.json'}",
    f"sh scripts/funding-release-report-validate.sh {bundle_dir / 'funding-release-report.json'}",
]

if evidence_status in {"ready_to_attach", "blocked_with_valid_evidence", "smoke_failed_with_valid_evidence"} and not errors:
    index_status = "passed"
elif errors:
    index_status = "failed"
else:
    index_status = "manual_inspection_required"

index = {
    "index_version": "funding_release_evidence_index_v0",
    "index_status": index_status,
    "bundle_dir": str(bundle_dir),
    "review_status": review_status,
    "audit_status": audit_status,
    "evidence_status": evidence_status,
    "ready_for_release_notes": bool(ready_for_release_notes),
    "ready_for_debug_review": bool(ready_for_debug_review),
    "release_gate_status": release_gate_status,
    "recommended_next_action": recommended_next_action,
    "bundle_exit_code": manifest.get("bundle_exit_code") if manifest else review.get("bundle_exit_code"),
    "report_exit_code": review.get("report_exit_code") or report.get("report_exit_code"),
    "validation_exit_code": manifest.get("validation_exit_code") if manifest else review.get("validation_exit_code"),
    "validation_status": validation.get("status") or review.get("validation_status"),
    "bundle_validation_status": bundle_validation.get("status") or review.get("bundle_validation_status"),
    "readiness_gate_status": review.get("readiness_gate_status") or report.get("readiness_gate_status"),
    "compare_gate_status": review.get("compare_gate_status") or report.get("compare_gate_status"),
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "artifacts": artifacts,
    "open_order": open_order,
    "review_commands": review_commands,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(index, ensure_ascii=False, indent=2))
elif output_format == "text":
    print("Funding release evidence index")
    print(f"- bundle_dir: {bundle_dir}")
    print(f"- index_status: {index_status}")
    print(f"- evidence_status: {text_value(evidence_status)}")
    print(f"- audit_status: {text_value(audit_status)}")
    print(f"- review_status: {text_value(review_status)}")
    print(f"- release_gate_status: {text_value(release_gate_status)}")
    print(f"- recommended_next_action: {recommended_next_action}")
    print("- open_order:")
    for row in open_order:
        print(f"  - {row['open_order']}. {row['filename']} exists={text_value(row['exists'])}")
    if errors:
        print(f"- errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
else:
    print("### Funding Release Evidence Index")
    print("")
    print(f"- index_status: {inline_code(index_status)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- audit_status: {inline_code(audit_status)}")
    print(f"- review_status: {inline_code(review_status)}")
    print(f"- release_gate_status: {inline_code(release_gate_status)}")
    print(f"- ready_for_release_notes: {inline_code(bool(ready_for_release_notes))}")
    print(f"- ready_for_debug_review: {inline_code(bool(ready_for_debug_review))}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Decision Signals")
    print(f"- bundle_exit_code: {inline_code(index['bundle_exit_code'])}")
    print(f"- report_exit_code: {inline_code(index['report_exit_code'])}")
    print(f"- validation_exit_code: {inline_code(index['validation_exit_code'])}")
    print(f"- validation_status: {inline_code(index['validation_status'])}")
    print(f"- bundle_validation_status: {inline_code(index['bundle_validation_status'])}")
    print(f"- readiness_gate_status: {inline_code(index['readiness_gate_status'])}")
    print(f"- compare_gate_status: {inline_code(index['compare_gate_status'])}")
    print("")
    print("#### Open First")
    print("| Order | Artifact | Purpose | Required | Exists | JSON | SHA-256 |")
    print("|---:|---|---|---:|---:|---:|---|")
    for row in open_order:
        print(
            f"| {markdown_cell(row['open_order'])} "
            f"| {markdown_cell(row['filename'])} "
            f"| {markdown_cell(row['purpose'])} "
            f"| {markdown_cell(row['required'])} "
            f"| {markdown_cell(row['exists'])} "
            f"| {markdown_cell(row['json_valid'])} "
            f"| {markdown_cell(row['sha256_short'])} |"
        )
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
    print("#### Local Review Commands")
    for command in review_commands:
        print(f"- `{command}`")
    if errors:
        print("")
        print("#### Index Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Index Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")

if errors:
    raise SystemExit(1)
PY
