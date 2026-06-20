#!/usr/bin/env sh
set -eu

BUNDLE_DIR="${1:-${FUNDING_RELEASE_AUDIT_DIR:-artifacts/funding-release}}"
AUDIT_FORMAT="${FUNDING_RELEASE_AUDIT_FORMAT:-text}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$AUDIT_FORMAT" in
  text|json|markdown) ;;
  *)
    printf 'FUNDING_RELEASE_AUDIT_FORMAT must be text, json or markdown.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence audit.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BUNDLE_DIR" "$AUDIT_FORMAT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle_dir = Path(sys.argv[1])
output_format = sys.argv[2]
errors = []
warnings = []

expected_files = [
    ("report", "funding-release-report.json", True, True),
    ("stdout", "funding-release-report.stdout.json", False, True),
    ("validation", "funding-release-validation.json", True, True),
    ("manifest", "funding-release-manifest.json", True, True),
    ("bundle_validation", "funding-release-bundle-validation.json", True, True),
    ("review", "funding-release-review.json", True, True),
    ("summary", "funding-release-summary.md", True, False),
    ("handoff", "funding-release-handoff.md", True, False),
]

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

def as_dict(value):
    return value if isinstance(value, dict) else {}

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

def file_info(name, filename, required, expect_json):
    path = bundle_dir / filename
    info = {
        "name": name,
        "filename": filename,
        "path": str(path),
        "required": required,
        "exists": path.is_file(),
        "json_expected": expect_json,
        "json_valid": None,
        "size_bytes": None,
        "sha256": None,
        "sha256_short": None,
    }
    if not path.is_file():
        if required:
            add_error(f"missing required artifact: {filename}")
        return info, None

    data = path.read_bytes()
    info["size_bytes"] = len(data)
    info["sha256"] = hashlib.sha256(data).hexdigest()
    info["sha256_short"] = info["sha256"][:12]
    if expect_json:
        try:
            parsed = json.loads(data.decode("utf-8"))
            info["json_valid"] = isinstance(parsed, dict)
            if not isinstance(parsed, dict):
                add_error(f"{filename} must be a JSON object")
                parsed = None
        except Exception as exc:
            info["json_valid"] = False
            add_error(f"{filename} is not valid JSON: {exc}")
            parsed = None
    else:
        parsed = None
    return info, parsed

if not bundle_dir.exists():
    raise SystemExit(f"Funding release evidence bundle directory not found: {bundle_dir}")
if not bundle_dir.is_dir():
    raise SystemExit(f"Funding release evidence bundle path is not a directory: {bundle_dir}")

artifacts = []
parsed = {}
for name, filename, required, expect_json in expected_files:
    info, value = file_info(name, filename, required, expect_json)
    artifacts.append(info)
    if value is not None:
        parsed[name] = value

report = as_dict(parsed.get("report"))
validation = as_dict(parsed.get("validation"))
manifest = as_dict(parsed.get("manifest"))
bundle_validation = as_dict(parsed.get("bundle_validation"))
review = as_dict(parsed.get("review"))

summary_path = bundle_dir / "funding-release-summary.md"
handoff_path = bundle_dir / "funding-release-handoff.md"
if summary_path.is_file():
    summary_text = summary_path.read_text(encoding="utf-8", errors="replace")
    if "### Funding Release Review" not in summary_text:
        add_error("funding-release-summary.md missing Funding Release Review heading")
else:
    summary_text = ""

if handoff_path.is_file():
    handoff_text = handoff_path.read_text(encoding="utf-8", errors="replace")
    if "### Funding Release Evidence Handoff" not in handoff_text:
        add_error("funding-release-handoff.md missing Funding Release Evidence Handoff heading")
else:
    handoff_text = ""

if report and report.get("report_version") != "funding_release_report_v0":
    add_error("report.report_version must be funding_release_report_v0")
if validation and validation.get("status") not in {"passed", "failed"}:
    add_error("validation.status must be passed or failed")
if manifest and manifest.get("manifest_version") != "funding_release_ci_bundle_v0":
    add_error("manifest.manifest_version must be funding_release_ci_bundle_v0")
if bundle_validation and bundle_validation.get("status") not in {"passed", "failed"}:
    add_error("bundle_validation.status must be passed or failed")
if review and review.get("review_version") != "funding_release_bundle_review_v0":
    add_error("review.review_version must be funding_release_bundle_review_v0")

artifact_status = as_dict(manifest.get("artifact_status"))
report_summary = as_dict(manifest.get("report_summary"))

if report and manifest:
    for field in ("release_gate_status", "exit_reason"):
        report_value = report.get(field)
        manifest_value = artifact_status.get(field)
        if report_value != manifest_value:
            add_error(f"report.{field} must match manifest.artifact_status.{field}")
    if report.get("report_exit_code") != manifest.get("report_exit_code"):
        add_error("report.report_exit_code must match manifest.report_exit_code")
    if report.get("readiness_gate_status") != report_summary.get("readiness_gate_status"):
        add_error("report.readiness_gate_status must match manifest.report_summary.readiness_gate_status")
    if report.get("compare_gate_status") != report_summary.get("compare_gate_status"):
        add_error("report.compare_gate_status must match manifest.report_summary.compare_gate_status")

if validation and manifest:
    if validation.get("status") != artifact_status.get("validation_status"):
        add_error("validation.status must match manifest.artifact_status.validation_status")
    if validation.get("error_count") != artifact_status.get("validation_error_count"):
        add_error("validation.error_count must match manifest.artifact_status.validation_error_count")

if bundle_validation and review:
    if bundle_validation.get("status") != review.get("bundle_validation_status"):
        add_error("bundle_validation.status must match review.bundle_validation_status")

if report and review:
    for field in ("release_gate_status", "exit_reason", "readiness_gate_status", "compare_gate_status"):
        if report.get(field) != review.get(field):
            add_error(f"report.{field} must match review.{field}")
    if report.get("report_exit_code") != review.get("report_exit_code"):
        add_error("report.report_exit_code must match review.report_exit_code")

release_gate_status = review.get("release_gate_status") or report.get("release_gate_status")
review_status = review.get("review_status")
bundle_validation_status = review.get("bundle_validation_status") or bundle_validation.get("status")

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

if bundle_validation_status != "passed":
    add_error("bundle validation status must be passed for a usable evidence bundle")

if handoff_text:
    if evidence_status not in handoff_text:
        add_error("funding-release-handoff.md evidence_status does not match audit-derived evidence_status")
    if review_status and review_status not in handoff_text:
        add_error("funding-release-handoff.md review_status does not match review artifact")

if summary_text and review_status and review_status not in summary_text:
    add_error("funding-release-summary.md review_status does not match review artifact")

audit_status = "failed" if errors else "passed"
ready_for_release_notes = evidence_status == "ready_to_attach"
ready_for_debug_review = evidence_status in {"blocked_with_valid_evidence", "smoke_failed_with_valid_evidence"}
recommended_next_action = review.get("recommended_next_action") or "Inspect Funding release evidence bundle"

audit = {
    "audit_version": "funding_release_evidence_audit_v0",
    "audit_status": audit_status,
    "bundle_dir": str(bundle_dir),
    "evidence_status": evidence_status,
    "ready_for_release_notes": ready_for_release_notes,
    "ready_for_debug_review": ready_for_debug_review,
    "review_status": review_status,
    "release_gate_status": release_gate_status,
    "recommended_next_action": recommended_next_action,
    "bundle_exit_code": manifest.get("bundle_exit_code") if manifest else None,
    "report_exit_code": review.get("report_exit_code") or report.get("report_exit_code"),
    "validation_exit_code": manifest.get("validation_exit_code") if manifest else None,
    "validation_status": validation.get("status") or review.get("validation_status"),
    "bundle_validation_status": bundle_validation_status,
    "readiness_gate_status": review.get("readiness_gate_status") or report.get("readiness_gate_status"),
    "compare_gate_status": review.get("compare_gate_status") or report.get("compare_gate_status"),
    "required_blocking_ids": review.get("required_blocking_ids") if isinstance(review.get("required_blocking_ids"), list) else [],
    "optional_blocking_ids": review.get("optional_blocking_ids") if isinstance(review.get("optional_blocking_ids"), list) else [],
    "artifacts": artifacts,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(audit, ensure_ascii=False, indent=2))
elif output_format == "markdown":
    print("### Funding Release Evidence Audit")
    print("")
    print(f"- audit_status: {inline_code(audit_status)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- ready_for_release_notes: {inline_code(ready_for_release_notes)}")
    print(f"- ready_for_debug_review: {inline_code(ready_for_debug_review)}")
    print(f"- review_status: {inline_code(review_status)}")
    print(f"- release_gate_status: {inline_code(release_gate_status)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Artifact Audit")
    print("| Artifact | Required | Exists | JSON | Size | SHA-256 |")
    print("|---|---:|---:|---:|---:|---|")
    for row in artifacts:
        print(
            f"| {markdown_cell(row['filename'])} "
            f"| {markdown_cell(row['required'])} "
            f"| {markdown_cell(row['exists'])} "
            f"| {markdown_cell(row['json_valid'])} "
            f"| {markdown_cell(row['size_bytes'])} "
            f"| {markdown_cell(row['sha256_short'])} |"
        )
    if errors:
        print("")
        print("#### Audit Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Audit Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")
else:
    print("Funding release evidence audit")
    print(f"- bundle_dir: {bundle_dir}")
    print(f"- audit_status: {audit_status}")
    print(f"- evidence_status: {evidence_status}")
    print(f"- ready_for_release_notes: {text_value(ready_for_release_notes)}")
    print(f"- ready_for_debug_review: {text_value(ready_for_debug_review)}")
    print(f"- review_status: {text_value(review_status)}")
    print(f"- release_gate_status: {text_value(release_gate_status)}")
    print(f"- recommended_next_action: {recommended_next_action}")
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
