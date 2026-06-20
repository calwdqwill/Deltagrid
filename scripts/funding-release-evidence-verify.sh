#!/usr/bin/env sh
set -eu

BUNDLE_DIR="${1:-${FUNDING_RELEASE_VERIFY_DIR:-artifacts/funding-release}}"
VERIFY_FORMAT="${FUNDING_RELEASE_VERIFY_FORMAT:-text}"
REQUIRE_RELEASE_NOTES_READY="${FUNDING_RELEASE_VERIFY_REQUIRE_RELEASE_NOTES_READY:-0}"
REQUIRE_DEBUG_READY="${FUNDING_RELEASE_VERIFY_REQUIRE_DEBUG_READY:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$VERIFY_FORMAT" in
  text|json|markdown) ;;
  *)
    printf 'FUNDING_RELEASE_VERIFY_FORMAT must be text, json or markdown.\n' >&2
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

require_bool "FUNDING_RELEASE_VERIFY_REQUIRE_RELEASE_NOTES_READY" "$REQUIRE_RELEASE_NOTES_READY"
require_bool "FUNDING_RELEASE_VERIFY_REQUIRE_DEBUG_READY" "$REQUIRE_DEBUG_READY"

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence verify.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BUNDLE_DIR" "$VERIFY_FORMAT" "$REQUIRE_RELEASE_NOTES_READY" "$REQUIRE_DEBUG_READY" <<'PY'
import json
import sys
from pathlib import Path

bundle_dir = Path(sys.argv[1])
output_format = sys.argv[2]
require_release_notes_ready = sys.argv[3] == "1"
require_debug_ready = sys.argv[4] == "1"

errors = []
warnings = []
checks = []

required_json_files = {
    "index": "funding-release-index.json",
    "audit": "funding-release-audit.json",
}

optional_json_files = {
    "review": "funding-release-review.json",
    "manifest": "funding-release-manifest.json",
    "bundle_validation": "funding-release-bundle-validation.json",
    "report": "funding-release-report.json",
    "validation": "funding-release-validation.json",
}

valid_evidence_statuses = {
    "ready_to_attach",
    "blocked_with_valid_evidence",
    "smoke_failed_with_valid_evidence",
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

def read_json_artifact(name, filename, required):
    path = bundle_dir / filename
    info = {
        "name": name,
        "filename": filename,
        "path": str(path),
        "required": required,
        "exists": path.is_file(),
        "json_valid": None,
    }
    if not path.is_file():
        status = "failed" if required else "skipped"
        add_check(f"{name}_exists", status, required, f"{filename} is missing")
        return info, {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        info["json_valid"] = False
        add_check(f"{name}_json_valid", "failed", required, f"{filename} is not valid JSON: {exc}")
        return info, {}
    if not isinstance(value, dict):
        info["json_valid"] = False
        add_check(f"{name}_json_object", "failed", required, f"{filename} must be a JSON object")
        return info, {}
    info["json_valid"] = True
    add_check(f"{name}_json_valid", "passed", required, f"{filename} is valid JSON")
    return info, value

def required_check(check_id, condition, detail_ok, detail_fail):
    if condition:
        add_check(check_id, "passed", True, detail_ok)
    else:
        add_check(check_id, "failed", True, detail_fail)

def optional_equal(check_id, left, right, label):
    if left is None or right is None:
        add_check(check_id, "skipped", False, f"{label} skipped because one side is missing")
        return
    if left == right:
        add_check(check_id, "passed", True, f"{label} matches: {left}")
    else:
        add_check(check_id, "failed", True, f"{label} mismatch: {left} != {right}")

if not bundle_dir.exists():
    raise SystemExit(f"Funding release evidence bundle directory not found: {bundle_dir}")
if not bundle_dir.is_dir():
    raise SystemExit(f"Funding release evidence bundle path is not a directory: {bundle_dir}")

artifacts = []
parsed = {}
for name, filename in required_json_files.items():
    info, value = read_json_artifact(name, filename, True)
    artifacts.append(info)
    parsed[name] = value

for name, filename in optional_json_files.items():
    info, value = read_json_artifact(name, filename, False)
    artifacts.append(info)
    if value:
        parsed[name] = value

index = as_dict(parsed.get("index"))
audit = as_dict(parsed.get("audit"))
review = as_dict(parsed.get("review"))
manifest = as_dict(parsed.get("manifest"))
bundle_validation = as_dict(parsed.get("bundle_validation"))
report = as_dict(parsed.get("report"))
validation = as_dict(parsed.get("validation"))

required_check(
    "index_version",
    index.get("index_version") == "funding_release_evidence_index_v0",
    "index version is funding_release_evidence_index_v0",
    f"index_version must be funding_release_evidence_index_v0, got {index.get('index_version')}",
)
required_check(
    "audit_version",
    audit.get("audit_version") == "funding_release_evidence_audit_v0",
    "audit version is funding_release_evidence_audit_v0",
    f"audit_version must be funding_release_evidence_audit_v0, got {audit.get('audit_version')}",
)
required_check(
    "index_status",
    index.get("index_status") == "passed",
    "index_status is passed",
    f"index_status must be passed, got {index.get('index_status')}",
)
required_check(
    "audit_status",
    audit.get("audit_status") == "passed",
    "audit_status is passed",
    f"audit_status must be passed, got {audit.get('audit_status')}",
)

index_evidence_status = index.get("evidence_status")
audit_evidence_status = audit.get("evidence_status")
evidence_status = audit_evidence_status or index_evidence_status
required_check(
    "evidence_status_supported",
    evidence_status in valid_evidence_statuses,
    f"evidence_status is {evidence_status}",
    f"evidence_status must be one of {sorted(valid_evidence_statuses)}, got {evidence_status}",
)
optional_equal("index_audit_evidence_status", index_evidence_status, audit_evidence_status, "index/audit evidence_status")
optional_equal("index_audit_review_status", index.get("review_status"), audit.get("review_status"), "index/audit review_status")
optional_equal("index_audit_release_gate_status", index.get("release_gate_status"), audit.get("release_gate_status"), "index/audit release_gate_status")
optional_equal("index_audit_report_exit_code", index.get("report_exit_code"), audit.get("report_exit_code"), "index/audit report_exit_code")
optional_equal("index_audit_release_notes_ready", index.get("ready_for_release_notes"), audit.get("ready_for_release_notes"), "index/audit ready_for_release_notes")
optional_equal("index_audit_debug_ready", index.get("ready_for_debug_review"), audit.get("ready_for_debug_review"), "index/audit ready_for_debug_review")

if review:
    required_check(
        "review_version",
        review.get("review_version") == "funding_release_bundle_review_v0",
        "review version is funding_release_bundle_review_v0",
        f"review_version must be funding_release_bundle_review_v0, got {review.get('review_version')}",
    )
    optional_equal("review_status_consistency", review.get("review_status"), audit.get("review_status"), "review/audit review_status")
    optional_equal("review_release_gate_consistency", review.get("release_gate_status"), audit.get("release_gate_status"), "review/audit release_gate_status")
    optional_equal("review_report_exit_consistency", review.get("report_exit_code"), audit.get("report_exit_code"), "review/audit report_exit_code")
else:
    add_check("review_optional", "skipped", False, "funding-release-review.json is not present")

if manifest:
    required_check(
        "manifest_version",
        manifest.get("manifest_version") == "funding_release_ci_bundle_v0",
        "manifest version is funding_release_ci_bundle_v0",
        f"manifest_version must be funding_release_ci_bundle_v0, got {manifest.get('manifest_version')}",
    )
    optional_equal("manifest_bundle_exit_consistency", manifest.get("bundle_exit_code"), index.get("bundle_exit_code"), "manifest/index bundle_exit_code")
    optional_equal("manifest_report_exit_consistency", manifest.get("report_exit_code"), audit.get("report_exit_code"), "manifest/audit report_exit_code")
else:
    add_check("manifest_optional", "skipped", False, "funding-release-manifest.json is not present")

if bundle_validation:
    required_check(
        "bundle_validation_status",
        bundle_validation.get("status") == "passed",
        "bundle validation status is passed",
        f"bundle validation status must be passed, got {bundle_validation.get('status')}",
    )

if validation:
    required_check(
        "report_validation_status",
        validation.get("status") == "passed",
        "report validation status is passed",
        f"report validation status must be passed, got {validation.get('status')}",
    )

if report:
    required_check(
        "report_version",
        report.get("report_version") == "funding_release_report_v0",
        "report version is funding_release_report_v0",
        f"report_version must be funding_release_report_v0, got {report.get('report_version')}",
    )
    optional_equal("report_release_gate_consistency", report.get("release_gate_status"), audit.get("release_gate_status"), "report/audit release_gate_status")
    optional_equal("report_exit_consistency", report.get("report_exit_code"), audit.get("report_exit_code"), "report/audit report_exit_code")

release_notes_ready = (
    not errors
    and evidence_status == "ready_to_attach"
    and bool(index.get("ready_for_release_notes"))
    and bool(audit.get("ready_for_release_notes"))
)
debug_review_ready = (
    not errors
    and evidence_status in {"blocked_with_valid_evidence", "smoke_failed_with_valid_evidence"}
    and bool(index.get("ready_for_debug_review"))
    and bool(audit.get("ready_for_debug_review"))
)
review_ready = release_notes_ready or debug_review_ready

if errors:
    verification_status = "failed"
    blocking_mode = "integrity_failed"
    exit_code = 1
elif require_release_notes_ready and not release_notes_ready:
    verification_status = "blocked"
    blocking_mode = "release_notes_not_ready"
    exit_code = 2
elif require_debug_ready and not review_ready:
    verification_status = "blocked"
    blocking_mode = "debug_review_not_ready"
    exit_code = 2
else:
    verification_status = "passed"
    blocking_mode = "none"
    exit_code = 0

recommended_next_action = (
    index.get("recommended_next_action")
    or audit.get("recommended_next_action")
    or review.get("recommended_next_action")
    or "Inspect Funding release evidence bundle"
)
if verification_status == "failed":
    recommended_next_action = "Regenerate Funding release evidence bundle"
elif blocking_mode == "release_notes_not_ready":
    recommended_next_action = "Resolve Funding release blockers before release notes handoff"
elif blocking_mode == "debug_review_not_ready":
    recommended_next_action = "Regenerate or inspect Funding release evidence before debug review"
elif release_notes_ready:
    recommended_next_action = "Attach Funding release evidence bundle to release notes"
elif debug_review_ready:
    recommended_next_action = "Use Funding release evidence bundle for blocker debug review"

required_blocking_ids = (
    as_list(index.get("required_blocking_ids"))
    or as_list(audit.get("required_blocking_ids"))
    or as_list(review.get("required_blocking_ids"))
)
optional_blocking_ids = (
    as_list(index.get("optional_blocking_ids"))
    or as_list(audit.get("optional_blocking_ids"))
    or as_list(review.get("optional_blocking_ids"))
)

verification = {
    "verification_version": "funding_release_evidence_verify_v0",
    "verification_status": verification_status,
    "blocking_mode": blocking_mode,
    "exit_code": exit_code,
    "bundle_dir": str(bundle_dir),
    "evidence_status": evidence_status,
    "index_status": index.get("index_status"),
    "audit_status": audit.get("audit_status"),
    "review_status": audit.get("review_status") or index.get("review_status") or review.get("review_status"),
    "release_gate_status": audit.get("release_gate_status") or index.get("release_gate_status") or review.get("release_gate_status"),
    "release_notes_ready": release_notes_ready,
    "debug_review_ready": debug_review_ready,
    "review_ready": review_ready,
    "require_release_notes_ready": require_release_notes_ready,
    "require_debug_ready": require_debug_ready,
    "recommended_next_action": recommended_next_action,
    "report_exit_code": audit.get("report_exit_code") or index.get("report_exit_code") or review.get("report_exit_code"),
    "bundle_exit_code": index.get("bundle_exit_code") or audit.get("bundle_exit_code") or review.get("bundle_exit_code"),
    "validation_status": audit.get("validation_status") or index.get("validation_status") or review.get("validation_status"),
    "bundle_validation_status": audit.get("bundle_validation_status") or index.get("bundle_validation_status") or review.get("bundle_validation_status"),
    "readiness_gate_status": audit.get("readiness_gate_status") or index.get("readiness_gate_status") or review.get("readiness_gate_status"),
    "compare_gate_status": audit.get("compare_gate_status") or index.get("compare_gate_status") or review.get("compare_gate_status"),
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "artifacts": artifacts,
    "checks": checks,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(verification, ensure_ascii=False, indent=2))
elif output_format == "markdown":
    print("### Funding Release Evidence Verify")
    print("")
    print(f"- verification_status: {inline_code(verification_status)}")
    print(f"- blocking_mode: {inline_code(blocking_mode)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- index_status: {inline_code(index.get('index_status'))}")
    print(f"- audit_status: {inline_code(audit.get('audit_status'))}")
    print(f"- review_status: {inline_code(verification['review_status'])}")
    print(f"- release_gate_status: {inline_code(verification['release_gate_status'])}")
    print(f"- release_notes_ready: {inline_code(release_notes_ready)}")
    print(f"- debug_review_ready: {inline_code(debug_review_ready)}")
    print(f"- review_ready: {inline_code(review_ready)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Gate Inputs")
    print(f"- require_release_notes_ready: {inline_code(require_release_notes_ready)}")
    print(f"- require_debug_ready: {inline_code(require_debug_ready)}")
    print(f"- report_exit_code: {inline_code(verification['report_exit_code'])}")
    print(f"- bundle_exit_code: {inline_code(verification['bundle_exit_code'])}")
    print(f"- validation_status: {inline_code(verification['validation_status'])}")
    print(f"- bundle_validation_status: {inline_code(verification['bundle_validation_status'])}")
    print("")
    print("#### Consistency Checks")
    print("| Check | Status | Required | Detail |")
    print("|---|---|---:|---|")
    for check in checks:
        print(
            f"| {markdown_cell(check['id'])} "
            f"| {markdown_cell(check['status'])} "
            f"| {markdown_cell(check['required'])} "
            f"| {markdown_cell(check['detail'])} |"
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
        print("#### Verify Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Verify Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")
else:
    print("Funding release evidence verify")
    print(f"- bundle_dir: {bundle_dir}")
    print(f"- verification_status: {verification_status}")
    print(f"- blocking_mode: {blocking_mode}")
    print(f"- evidence_status: {text_value(evidence_status)}")
    print(f"- release_notes_ready: {text_value(release_notes_ready)}")
    print(f"- debug_review_ready: {text_value(debug_review_ready)}")
    print(f"- review_ready: {text_value(review_ready)}")
    print(f"- recommended_next_action: {recommended_next_action}")
    print(f"- errors: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
    if warnings:
        print(f"- warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")

raise SystemExit(exit_code)
PY
