#!/usr/bin/env sh
set -eu

BUNDLE_DIR="${1:-${FUNDING_RELEASE_NOTES_DIR:-artifacts/funding-release}}"
NOTES_FORMAT="${FUNDING_RELEASE_NOTES_FORMAT:-markdown}"
REQUIRE_READY="${FUNDING_RELEASE_NOTES_REQUIRE_READY:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$NOTES_FORMAT" in
  text|json|markdown) ;;
  *)
    printf 'FUNDING_RELEASE_NOTES_FORMAT must be text, json or markdown.\n' >&2
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

require_bool "FUNDING_RELEASE_NOTES_REQUIRE_READY" "$REQUIRE_READY"

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence notes.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BUNDLE_DIR" "$NOTES_FORMAT" "$REQUIRE_READY" <<'PY'
import json
import sys
from pathlib import Path

bundle_dir = Path(sys.argv[1])
output_format = sys.argv[2]
require_ready = sys.argv[3] == "1"

errors = []
warnings = []
checks = []

json_artifacts = [
    ("verify", "funding-release-verify.json", True, "Final local verdict"),
    ("index", "funding-release-index.json", False, "Bundle entrypoint"),
    ("audit", "funding-release-audit.json", False, "Bundle consistency audit"),
    ("review", "funding-release-review.json", False, "Runbook review"),
    ("manifest", "funding-release-manifest.json", False, "Bundle manifest"),
    ("report", "funding-release-report.json", False, "Compact report"),
    ("validation", "funding-release-validation.json", False, "Report validation"),
    ("bundle_validation", "funding-release-bundle-validation.json", False, "Manifest validation"),
]

markdown_artifacts = [
    ("notes_markdown", "funding-release-notes.md", "Paste-ready notes"),
    ("index_markdown", "funding-release-index.md", "Review entrypoint"),
    ("verify_markdown", "funding-release-verify.md", "Verify readout"),
    ("audit_markdown", "funding-release-audit.md", "Audit readout"),
    ("summary", "funding-release-summary.md", "GitHub/release summary"),
    ("handoff", "funding-release-handoff.md", "Release handoff checklist"),
]

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
        "id": name,
        "filename": filename,
        "path": str(path),
        "required_for_notes": required,
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

def file_reference(filename, purpose, open_order):
    path = bundle_dir / filename
    return {
        "filename": filename,
        "path": str(path),
        "exists": path.is_file(),
        "purpose": purpose,
        "open_order": open_order,
    }

def optional_equal(check_id, left, right, detail):
    if left is None or right is None:
        add_check(check_id, "skipped", False, f"{detail} skipped because one side is missing")
        return
    if left == right:
        add_check(check_id, "passed", True, f"{detail} matches: {left}")
    else:
        add_check(check_id, "failed", True, f"{detail} mismatch: {left} != {right}")

parsed = {}
json_refs = []

if not bundle_dir.exists():
    add_check("bundle_dir_exists", "failed", True, f"{bundle_dir} does not exist")
elif not bundle_dir.is_dir():
    add_check("bundle_dir_is_dir", "failed", True, f"{bundle_dir} is not a directory")
else:
    add_check("bundle_dir_exists", "passed", True, f"{bundle_dir} is available")
    for name, filename, required, _purpose in json_artifacts:
        info, value = read_json_artifact(name, filename, required)
        json_refs.append(info)
        if value:
            parsed[name] = value

verify = as_dict(parsed.get("verify"))
index = as_dict(parsed.get("index"))
audit = as_dict(parsed.get("audit"))
review = as_dict(parsed.get("review"))
manifest = as_dict(parsed.get("manifest"))
report = as_dict(parsed.get("report"))
validation = as_dict(parsed.get("validation"))
bundle_validation = as_dict(parsed.get("bundle_validation"))

if verify:
    if verify.get("verification_version") == "funding_release_evidence_verify_v0":
        add_check("verify_version", "passed", True, "verify version is funding_release_evidence_verify_v0")
    else:
        add_check(
            "verify_version",
            "failed",
            True,
            f"verification_version must be funding_release_evidence_verify_v0, got {verify.get('verification_version')}",
        )

if index:
    if index.get("index_version") == "funding_release_evidence_index_v0":
        add_check("index_version", "passed", True, "index version is funding_release_evidence_index_v0")
    else:
        add_check("index_version", "failed", True, f"index_version mismatch: {index.get('index_version')}")
    optional_equal(
        "verify_index_evidence_status",
        verify.get("evidence_status"),
        index.get("evidence_status"),
        "verify/index evidence_status",
    )
    optional_equal(
        "verify_index_release_notes_ready",
        verify.get("release_notes_ready"),
        index.get("ready_for_release_notes"),
        "verify/index release notes readiness",
    )
    optional_equal(
        "verify_index_debug_ready",
        verify.get("debug_review_ready"),
        index.get("ready_for_debug_review"),
        "verify/index debug readiness",
    )

if audit:
    if audit.get("audit_version") == "funding_release_evidence_audit_v0":
        add_check("audit_version", "passed", True, "audit version is funding_release_evidence_audit_v0")
    else:
        add_check("audit_version", "failed", True, f"audit_version mismatch: {audit.get('audit_version')}")
    optional_equal(
        "verify_audit_evidence_status",
        verify.get("evidence_status"),
        audit.get("evidence_status"),
        "verify/audit evidence_status",
    )
    optional_equal(
        "verify_audit_release_notes_ready",
        verify.get("release_notes_ready"),
        audit.get("ready_for_release_notes"),
        "verify/audit release notes readiness",
    )
    optional_equal(
        "verify_audit_debug_ready",
        verify.get("debug_review_ready"),
        audit.get("ready_for_debug_review"),
        "verify/audit debug readiness",
    )

if review:
    if review.get("review_version") == "funding_release_bundle_review_v0":
        add_check("review_version", "passed", False, "review version is funding_release_bundle_review_v0")
    else:
        add_check("review_version", "warning", False, f"review_version mismatch: {review.get('review_version')}")

if manifest:
    if manifest.get("manifest_version") == "funding_release_ci_bundle_v0":
        add_check("manifest_version", "passed", False, "manifest version is funding_release_ci_bundle_v0")
    else:
        add_check("manifest_version", "warning", False, f"manifest_version mismatch: {manifest.get('manifest_version')}")

if report and report.get("report_version") != "funding_release_report_v0":
    add_check("report_version", "warning", False, f"report_version mismatch: {report.get('report_version')}")
if validation and validation.get("status") not in {"passed", "failed"}:
    add_check("validation_status", "warning", False, f"validation.status is unexpected: {validation.get('status')}")
if bundle_validation and bundle_validation.get("status") not in {"passed", "failed"}:
    add_check("bundle_validation_status", "warning", False, f"bundle_validation.status is unexpected: {bundle_validation.get('status')}")

verification_status = verify.get("verification_status")
blocking_mode = verify.get("blocking_mode")
evidence_status = verify.get("evidence_status")
release_notes_ready = bool(verify.get("release_notes_ready"))
debug_review_ready = bool(verify.get("debug_review_ready"))
review_ready = bool(verify.get("review_ready"))
review_status = verify.get("review_status")
release_gate_status = verify.get("release_gate_status")
readiness_gate_status = verify.get("readiness_gate_status")
compare_gate_status = verify.get("compare_gate_status")
report_exit_code = verify.get("report_exit_code")
bundle_exit_code = verify.get("bundle_exit_code")
validation_status = verify.get("validation_status")
bundle_validation_status = verify.get("bundle_validation_status")
recommended_next_action = verify.get("recommended_next_action") or "Inspect Funding release evidence bundle"
required_blocking_ids = as_list(verify.get("required_blocking_ids"))
optional_blocking_ids = as_list(verify.get("optional_blocking_ids"))

if not required_blocking_ids:
    required_blocking_ids = as_list(index.get("required_blocking_ids")) or as_list(audit.get("required_blocking_ids")) or as_list(review.get("required_blocking_ids"))
if not optional_blocking_ids:
    optional_blocking_ids = as_list(index.get("optional_blocking_ids")) or as_list(audit.get("optional_blocking_ids")) or as_list(review.get("optional_blocking_ids"))

artifact_references = []
open_order = 1
for _name, filename, _required, purpose in json_artifacts:
    artifact_references.append(file_reference(filename, purpose, open_order))
    open_order += 1
for _name, filename, purpose in markdown_artifacts:
    artifact_references.append(file_reference(filename, purpose, open_order))
    open_order += 1

if errors or verification_status == "failed":
    notes_status = "failed"
    notes_mode = "integrity_failed"
    exit_code = 1
elif verification_status == "passed" and release_notes_ready:
    notes_status = "ready"
    notes_mode = "release_notes"
    exit_code = 0
elif debug_review_ready:
    notes_status = "blocked"
    notes_mode = "debug_review"
    exit_code = 2 if require_ready else 0
elif verification_status == "blocked":
    notes_status = "blocked"
    notes_mode = blocking_mode or "release_notes_not_ready"
    exit_code = 2 if require_ready else 0
else:
    notes_status = "blocked"
    notes_mode = "manual_review"
    exit_code = 2 if require_ready else 0

if require_ready and notes_status != "ready" and exit_code == 0:
    exit_code = 2

release_artifacts = [
    "funding-release-index.md",
    "funding-release-verify.md",
    "funding-release-audit.md",
    "funding-release-summary.md",
    "funding-release-handoff.md",
]
debug_artifacts = [
    "funding-release-notes.md",
    "funding-release-verify.json",
    "funding-release-index.json",
    "funding-release-audit.json",
    "funding-release-review.json",
    "funding-release-report.json",
]

release_notes_snippet = [
    "Funding release evidence bundle verified for release notes.",
    f"Evidence status: {text_value(evidence_status)}.",
    f"Verification status: {text_value(verification_status)}, release notes ready: {text_value(release_notes_ready)}.",
    f"Release gate status: {text_value(release_gate_status)}.",
    f"Attach artifacts: {', '.join(release_artifacts)}.",
]

debug_review_snippet = [
    "Funding release evidence bundle is not ready for release notes.",
    f"Evidence status: {text_value(evidence_status)}.",
    f"Verification status: {text_value(verification_status)}, debug review ready: {text_value(debug_review_ready)}.",
    f"Recommended next action: {recommended_next_action}.",
    f"Required blockers: {', '.join(required_blocking_ids) if required_blocking_ids else 'none'}.",
    f"Optional blockers: {', '.join(optional_blocking_ids) if optional_blocking_ids else 'none'}.",
    f"Open artifacts: {', '.join(debug_artifacts)}.",
]

notes = {
    "notes_version": "funding_release_evidence_notes_v0",
    "notes_status": notes_status,
    "notes_mode": notes_mode,
    "exit_code": exit_code,
    "bundle_dir": str(bundle_dir),
    "verification_status": verification_status,
    "blocking_mode": blocking_mode,
    "evidence_status": evidence_status,
    "release_notes_ready": release_notes_ready,
    "debug_review_ready": debug_review_ready,
    "review_ready": review_ready,
    "require_ready": require_ready,
    "review_status": review_status,
    "release_gate_status": release_gate_status,
    "readiness_gate_status": readiness_gate_status,
    "compare_gate_status": compare_gate_status,
    "report_exit_code": report_exit_code,
    "bundle_exit_code": bundle_exit_code,
    "validation_status": validation_status,
    "bundle_validation_status": bundle_validation_status,
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "recommended_next_action": recommended_next_action,
    "release_notes_snippet": release_notes_snippet if notes_status == "ready" else [],
    "debug_review_snippet": debug_review_snippet if notes_status != "ready" else [],
    "artifact_references": artifact_references,
    "checks": checks,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(notes, ensure_ascii=False, indent=2))
elif output_format == "markdown":
    print("### Funding Release Evidence Notes")
    print("")
    print(f"- notes_status: {inline_code(notes_status)}")
    print(f"- notes_mode: {inline_code(notes_mode)}")
    print(f"- verification_status: {inline_code(verification_status)}")
    print(f"- blocking_mode: {inline_code(blocking_mode)}")
    print(f"- evidence_status: {inline_code(evidence_status)}")
    print(f"- release_notes_ready: {inline_code(release_notes_ready)}")
    print(f"- debug_review_ready: {inline_code(debug_review_ready)}")
    print(f"- review_ready: {inline_code(review_ready)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    if notes_status == "ready":
        print("#### Release Notes Snippet")
        for item in release_notes_snippet:
            print(f"- {item}")
    elif notes_status == "failed":
        print("#### Integrity Failure")
        print("- Regenerate Funding release evidence bundle before release notes or debug review.")
    else:
        print("#### Debug Review Snippet")
        for item in debug_review_snippet:
            print(f"- {item}")
    print("")
    print("#### Blockers")
    print(f"- required: {inline_code(', '.join(required_blocking_ids) if required_blocking_ids else 'none')}")
    print(f"- optional: {inline_code(', '.join(optional_blocking_ids) if optional_blocking_ids else 'none')}")
    print("")
    print("#### Artifact Checklist")
    print("| Order | Artifact | Exists | Purpose |")
    print("|---:|---|---:|---|")
    for artifact in sorted(artifact_references, key=lambda row: row["open_order"]):
        print(
            f"| {markdown_cell(artifact['open_order'])} "
            f"| {markdown_cell(artifact['filename'])} "
            f"| {markdown_cell(artifact['exists'])} "
            f"| {markdown_cell(artifact['purpose'])} |"
        )
    if errors:
        print("")
        print("#### Notes Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Notes Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")
else:
    print("Funding release evidence notes")
    print(f"- bundle_dir: {bundle_dir}")
    print(f"- notes_status: {notes_status}")
    print(f"- notes_mode: {notes_mode}")
    print(f"- verification_status: {text_value(verification_status)}")
    print(f"- evidence_status: {text_value(evidence_status)}")
    print(f"- release_notes_ready: {text_value(release_notes_ready)}")
    print(f"- debug_review_ready: {text_value(debug_review_ready)}")
    print(f"- recommended_next_action: {recommended_next_action}")
    if notes_status == "ready":
        print("- release_notes_snippet:")
        for item in release_notes_snippet:
            print(f"  - {item}")
    elif notes_status == "failed":
        print("- integrity_failure: regenerate Funding release evidence bundle")
    else:
        print("- debug_review_snippet:")
        for item in debug_review_snippet:
            print(f"  - {item}")
    if errors:
        print(f"- errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    if warnings:
        print(f"- warnings: {len(warnings)}")
        for warning in warnings:
            print(f"  - {warning}")

raise SystemExit(exit_code)
PY
