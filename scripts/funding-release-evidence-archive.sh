#!/usr/bin/env sh
set -eu

BUNDLE_DIR="${1:-${FUNDING_RELEASE_ARCHIVE_DIR:-artifacts/funding-release}}"
ARCHIVE_FORMAT="${FUNDING_RELEASE_ARCHIVE_FORMAT:-markdown}"
REQUIRE_RELEASE_READY="${FUNDING_RELEASE_ARCHIVE_REQUIRE_RELEASE_READY:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$ARCHIVE_FORMAT" in
  markdown|text|json) ;;
  *)
    printf 'FUNDING_RELEASE_ARCHIVE_FORMAT must be markdown, text or json.\n' >&2
    exit 1
    ;;
esac

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

require_bool "FUNDING_RELEASE_ARCHIVE_REQUIRE_RELEASE_READY" "$REQUIRE_RELEASE_READY"

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence archive.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BUNDLE_DIR" "$ARCHIVE_FORMAT" "$REQUIRE_RELEASE_READY" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle_dir = Path(sys.argv[1])
output_format = sys.argv[2]
require_release_ready = sys.argv[3] == "1"

errors = []
warnings = []
checks = []

expected_artifacts = [
    {
        "id": "index_markdown",
        "filename": "funding-release-index.md",
        "required": True,
        "json": False,
        "open_order": 1,
        "purpose": "Reviewer entrypoint",
    },
    {
        "id": "verify_markdown",
        "filename": "funding-release-verify.md",
        "required": True,
        "json": False,
        "open_order": 2,
        "purpose": "Final local verdict readout",
    },
    {
        "id": "notes_markdown",
        "filename": "funding-release-notes.md",
        "required": True,
        "json": False,
        "open_order": 3,
        "purpose": "Paste-ready release/debug notes",
    },
    {
        "id": "summary",
        "filename": "funding-release-summary.md",
        "required": True,
        "json": False,
        "open_order": 4,
        "purpose": "GitHub/release summary",
    },
    {
        "id": "handoff",
        "filename": "funding-release-handoff.md",
        "required": True,
        "json": False,
        "open_order": 5,
        "purpose": "Release handoff checklist",
    },
    {
        "id": "audit_markdown",
        "filename": "funding-release-audit.md",
        "required": True,
        "json": False,
        "open_order": 6,
        "purpose": "Human-readable bundle audit",
    },
    {
        "id": "compare_markdown",
        "filename": "funding-release-compare.md",
        "required": False,
        "json": False,
        "open_order": 7,
        "purpose": "Optional offline bundle compare",
    },
    {
        "id": "report",
        "filename": "funding-release-report.json",
        "required": True,
        "json": True,
        "open_order": 8,
        "purpose": "Compact release report",
    },
    {
        "id": "review",
        "filename": "funding-release-review.json",
        "required": True,
        "json": True,
        "open_order": 9,
        "purpose": "Runbook review JSON",
    },
    {
        "id": "manifest",
        "filename": "funding-release-manifest.json",
        "required": True,
        "json": True,
        "open_order": 10,
        "purpose": "Evidence bundle manifest",
    },
    {
        "id": "validation",
        "filename": "funding-release-validation.json",
        "required": True,
        "json": True,
        "open_order": 11,
        "purpose": "Compact report validation result",
    },
    {
        "id": "bundle_validation",
        "filename": "funding-release-bundle-validation.json",
        "required": True,
        "json": True,
        "open_order": 12,
        "purpose": "Manifest/checksum validation",
    },
    {
        "id": "audit",
        "filename": "funding-release-audit.json",
        "required": True,
        "json": True,
        "open_order": 13,
        "purpose": "Machine-readable bundle audit",
    },
    {
        "id": "index",
        "filename": "funding-release-index.json",
        "required": True,
        "json": True,
        "open_order": 14,
        "purpose": "Machine-readable bundle entrypoint",
    },
    {
        "id": "verify",
        "filename": "funding-release-verify.json",
        "required": True,
        "json": True,
        "open_order": 15,
        "purpose": "Machine-readable final verdict",
    },
    {
        "id": "notes",
        "filename": "funding-release-notes.json",
        "required": True,
        "json": True,
        "open_order": 16,
        "purpose": "Machine-readable release/debug notes",
    },
    {
        "id": "compare",
        "filename": "funding-release-compare.json",
        "required": False,
        "json": True,
        "open_order": 17,
        "purpose": "Optional machine-readable bundle compare",
    },
    {
        "id": "stdout",
        "filename": "funding-release-report.stdout.json",
        "required": False,
        "json": True,
        "open_order": 18,
        "purpose": "Optional raw report stdout",
    },
]

version_expectations = {
    "report": ("report_version", "funding_release_report_v0", True),
    "manifest": ("manifest_version", "funding_release_ci_bundle_v0", True),
    "review": ("review_version", "funding_release_bundle_review_v0", True),
    "audit": ("audit_version", "funding_release_evidence_audit_v0", True),
    "index": ("index_version", "funding_release_evidence_index_v0", True),
    "verify": ("verification_version", "funding_release_evidence_verify_v0", True),
    "notes": ("notes_version", "funding_release_evidence_notes_v0", True),
    "compare": ("compare_version", "funding_release_evidence_compare_v0", False),
}

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

def add_check(check_id, status, required, detail):
    checks.append({
        "id": check_id,
        "status": status,
        "required": required,
        "detail": detail,
    })
    if required and status == "failed":
        add_error(f"{check_id}: {detail}")
    elif status == "warning":
        add_warning(f"{check_id}: {detail}")

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

def read_file_info(spec):
    path = bundle_dir / spec["filename"]
    info = {
        "id": spec["id"],
        "filename": spec["filename"],
        "path": str(path),
        "required_for_archive": spec["required"],
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
            add_check(f"{spec['id']}_exists", "failed", True, f"{spec['filename']} is missing")
        else:
            add_check(f"{spec['id']}_exists", "skipped", False, f"{spec['filename']} is not present")
        return info, parsed

    data = path.read_bytes()
    info["size_bytes"] = len(data)
    info["sha256"] = hashlib.sha256(data).hexdigest()
    info["sha256_short"] = info["sha256"][:12]
    add_check(f"{spec['id']}_exists", "passed", spec["required"], f"{spec['filename']} is present")

    if spec["json"]:
        try:
            value = json.loads(data.decode("utf-8"))
        except Exception as exc:
            info["json_valid"] = False
            if spec["required"]:
                add_check(f"{spec['id']}_json_valid", "failed", True, f"{spec['filename']} is not valid JSON: {exc}")
            else:
                add_check(f"{spec['id']}_json_valid", "warning", False, f"{spec['filename']} is not valid JSON: {exc}")
            return info, parsed
        if not isinstance(value, dict):
            info["json_valid"] = False
            if spec["required"]:
                add_check(f"{spec['id']}_json_object", "failed", True, f"{spec['filename']} must be a JSON object")
            else:
                add_check(f"{spec['id']}_json_object", "warning", False, f"{spec['filename']} must be a JSON object")
            return info, parsed
        info["json_valid"] = True
        parsed = value
        add_check(f"{spec['id']}_json_valid", "passed", spec["required"], f"{spec['filename']} is valid JSON")
    return info, parsed

def required_equal(check_id, left, right, label):
    if left is None or right is None:
        add_check(check_id, "skipped", False, f"{label} skipped because one side is missing")
        return
    if left == right:
        add_check(check_id, "passed", True, f"{label} matches: {left}")
    else:
        add_check(check_id, "failed", True, f"{label} mismatch: {left} != {right}")

if not bundle_dir.exists():
    add_check("bundle_dir_exists", "failed", True, f"{bundle_dir} does not exist")
elif not bundle_dir.is_dir():
    add_check("bundle_dir_is_dir", "failed", True, f"{bundle_dir} is not a directory")
else:
    add_check("bundle_dir_exists", "passed", True, f"{bundle_dir} is available")

artifacts = []
parsed = {}
if bundle_dir.exists() and bundle_dir.is_dir():
    for spec in expected_artifacts:
        row, value = read_file_info(spec)
        artifacts.append(row)
        if value is not None:
            parsed[spec["id"]] = value

for artifact_id, (field, expected, required) in version_expectations.items():
    artifact = as_dict(parsed.get(artifact_id))
    if not artifact:
        continue
    actual = artifact.get(field)
    if actual == expected:
        add_check(f"{artifact_id}_version", "passed", required, f"{field} is {expected}")
    else:
        status = "failed" if required else "warning"
        add_check(f"{artifact_id}_version", status, required, f"{field} must be {expected}, got {actual}")

report = as_dict(parsed.get("report"))
validation = as_dict(parsed.get("validation"))
manifest = as_dict(parsed.get("manifest"))
bundle_validation = as_dict(parsed.get("bundle_validation"))
review = as_dict(parsed.get("review"))
audit = as_dict(parsed.get("audit"))
index = as_dict(parsed.get("index"))
verify = as_dict(parsed.get("verify"))
notes = as_dict(parsed.get("notes"))
compare = as_dict(parsed.get("compare"))

if validation and validation.get("status") != "passed":
    add_check("validation_status", "failed", True, f"validation.status must be passed, got {validation.get('status')}")
if bundle_validation and bundle_validation.get("status") != "passed":
    add_check(
        "bundle_validation_status",
        "failed",
        True,
        f"bundle_validation.status must be passed, got {bundle_validation.get('status')}",
    )
if audit and audit.get("audit_status") != "passed":
    add_check("audit_status", "failed", True, f"audit_status must be passed, got {audit.get('audit_status')}")
if index and index.get("index_status") != "passed":
    add_check("index_status", "failed", True, f"index_status must be passed, got {index.get('index_status')}")
if verify and verify.get("verification_status") == "failed":
    add_check("verification_status", "failed", True, "verification_status is failed")
if notes and notes.get("notes_status") == "failed":
    add_check("notes_status", "failed", True, "notes_status is failed")

if verify and notes:
    required_equal(
        "verify_notes_verification_status",
        verify.get("verification_status"),
        notes.get("verification_status"),
        "verify/notes verification_status",
    )
    required_equal(
        "verify_notes_release_notes_ready",
        verify.get("release_notes_ready"),
        notes.get("release_notes_ready"),
        "verify/notes release notes readiness",
    )
    required_equal(
        "verify_notes_debug_review_ready",
        verify.get("debug_review_ready"),
        notes.get("debug_review_ready"),
        "verify/notes debug readiness",
    )

if verify and index:
    required_equal(
        "verify_index_evidence_status",
        verify.get("evidence_status"),
        index.get("evidence_status"),
        "verify/index evidence_status",
    )
if verify and audit:
    required_equal(
        "verify_audit_evidence_status",
        verify.get("evidence_status"),
        audit.get("evidence_status"),
        "verify/audit evidence_status",
    )
if compare and compare.get("compare_status") == "failed":
    add_check("compare_status", "warning", False, "optional compare artifact has failed status")

release_notes_ready = bool(verify.get("release_notes_ready")) and bool(notes.get("release_notes_ready"))
debug_review_ready = bool(verify.get("debug_review_ready")) and bool(notes.get("debug_review_ready"))
verification_status = verify.get("verification_status")
notes_status = notes.get("notes_status")
notes_mode = notes.get("notes_mode")
evidence_status = verify.get("evidence_status") or index.get("evidence_status") or audit.get("evidence_status")
release_gate_status = verify.get("release_gate_status") or review.get("release_gate_status") or report.get("release_gate_status")
readiness_gate_status = verify.get("readiness_gate_status") or review.get("readiness_gate_status") or report.get("readiness_gate_status")
compare_gate_status = verify.get("compare_gate_status") or review.get("compare_gate_status") or report.get("compare_gate_status")
report_exit_code = verify.get("report_exit_code") or review.get("report_exit_code") or report.get("report_exit_code")
bundle_exit_code = verify.get("bundle_exit_code") or index.get("bundle_exit_code") or review.get("bundle_exit_code") or manifest.get("bundle_exit_code")
validation_status = verify.get("validation_status") or audit.get("validation_status") or validation.get("status")
bundle_validation_status = verify.get("bundle_validation_status") or audit.get("bundle_validation_status") or bundle_validation.get("status")
required_blocking_ids = (
    as_list(verify.get("required_blocking_ids"))
    or as_list(notes.get("required_blocking_ids"))
    or as_list(index.get("required_blocking_ids"))
    or as_list(audit.get("required_blocking_ids"))
    or as_list(review.get("required_blocking_ids"))
)
optional_blocking_ids = (
    as_list(verify.get("optional_blocking_ids"))
    or as_list(notes.get("optional_blocking_ids"))
    or as_list(index.get("optional_blocking_ids"))
    or as_list(audit.get("optional_blocking_ids"))
    or as_list(review.get("optional_blocking_ids"))
)

file_count = sum(1 for row in artifacts if row["exists"])
required_file_count = sum(1 for row in artifacts if row["required_for_archive"])
optional_file_count = len(artifacts) - required_file_count
missing_required_count = sum(1 for row in artifacts if row["required_for_archive"] and not row["exists"])
json_valid_count = sum(1 for row in artifacts if row["json_valid"] is True)
json_invalid_count = sum(1 for row in artifacts if row["json_valid"] is False)
total_size_bytes = sum(row["size_bytes"] or 0 for row in artifacts)

if errors:
    archive_status = "failed"
    archive_mode = "integrity_failed"
    exit_code = 1
elif require_release_ready and not release_notes_ready:
    archive_status = "blocked"
    archive_mode = "debug_review" if debug_review_ready else "manual_review"
    exit_code = 2
elif release_notes_ready:
    archive_status = "complete"
    archive_mode = "release_ready"
    exit_code = 0
elif debug_review_ready:
    archive_status = "complete"
    archive_mode = "debug_review"
    exit_code = 0
else:
    archive_status = "complete"
    archive_mode = "manual_review"
    exit_code = 0

if archive_status == "failed":
    recommended_next_action = "Regenerate Funding release evidence bundle before archive handoff"
elif archive_status == "blocked":
    recommended_next_action = "Resolve Funding release blockers before release-ready archive handoff"
elif release_notes_ready:
    recommended_next_action = "Attach Funding release evidence bundle and archive to release notes"
elif debug_review_ready:
    recommended_next_action = "Use Funding release archive for blocker debug review"
else:
    recommended_next_action = "Inspect Funding release archive manually"

archive = {
    "archive_version": "funding_release_evidence_archive_v0",
    "archive_status": archive_status,
    "archive_mode": archive_mode,
    "exit_code": exit_code,
    "bundle_dir": str(bundle_dir),
    "require_release_ready": require_release_ready,
    "release_notes_ready": release_notes_ready,
    "debug_review_ready": debug_review_ready,
    "verification_status": verification_status,
    "notes_status": notes_status,
    "notes_mode": notes_mode,
    "evidence_status": evidence_status,
    "release_gate_status": release_gate_status,
    "readiness_gate_status": readiness_gate_status,
    "compare_gate_status": compare_gate_status,
    "report_exit_code": report_exit_code,
    "bundle_exit_code": bundle_exit_code,
    "validation_status": validation_status,
    "bundle_validation_status": bundle_validation_status,
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "file_count": file_count,
    "required_file_count": required_file_count,
    "optional_file_count": optional_file_count,
    "missing_required_count": missing_required_count,
    "json_valid_count": json_valid_count,
    "json_invalid_count": json_invalid_count,
    "total_size_bytes": total_size_bytes,
    "recommended_next_action": recommended_next_action,
    "artifacts": sorted(artifacts, key=lambda row: (row["open_order"], row["filename"])),
    "checks": checks,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(archive, ensure_ascii=False, indent=2))
elif output_format == "text":
    print("Funding release evidence archive")
    print(f"- bundle_dir: {bundle_dir}")
    print(f"- archive_status: {archive_status}")
    print(f"- archive_mode: {archive_mode}")
    print(f"- release_notes_ready: {text_value(release_notes_ready)}")
    print(f"- debug_review_ready: {text_value(debug_review_ready)}")
    print(f"- verification_status: {text_value(verification_status)}")
    print(f"- notes_status: {text_value(notes_status)}")
    print(f"- file_count: {file_count}")
    print(f"- missing_required_count: {missing_required_count}")
    print(f"- total_size_bytes: {total_size_bytes}")
    print(f"- recommended_next_action: {recommended_next_action}")
    if errors:
        print(f"- errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    if warnings:
        print(f"- warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")
else:
    print("### Funding Release Evidence Archive")
    print("")
    print(f"- archive_status: {inline_code(archive_status)}")
    print(f"- archive_mode: {inline_code(archive_mode)}")
    print(f"- release_notes_ready: {inline_code(release_notes_ready)}")
    print(f"- debug_review_ready: {inline_code(debug_review_ready)}")
    print(f"- verification_status: {inline_code(verification_status)}")
    print(f"- notes_status: {inline_code(notes_status)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Archive Summary")
    print(f"- file_count: {inline_code(file_count)}")
    print(f"- required_file_count: {inline_code(required_file_count)}")
    print(f"- missing_required_count: {inline_code(missing_required_count)}")
    print(f"- json_valid_count: {inline_code(json_valid_count)}")
    print(f"- json_invalid_count: {inline_code(json_invalid_count)}")
    print(f"- total_size_bytes: {inline_code(total_size_bytes)}")
    print("")
    print("#### Archive Files")
    print("| Order | Artifact | Required | Exists | JSON | Size | SHA-256 |")
    print("|---:|---|---:|---:|---:|---:|---|")
    for row in archive["artifacts"]:
        print(
            f"| {markdown_cell(row['open_order'])} "
            f"| {markdown_cell(row['filename'])} "
            f"| {markdown_cell(row['required_for_archive'])} "
            f"| {markdown_cell(row['exists'])} "
            f"| {markdown_cell(row['json_valid'])} "
            f"| {markdown_cell(row['size_bytes'])} "
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
    if errors:
        print("")
        print("#### Archive Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Archive Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")

raise SystemExit(exit_code)
PY
