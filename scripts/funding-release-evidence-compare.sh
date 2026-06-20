#!/usr/bin/env sh
set -eu

BASE_DIR="${1:-${FUNDING_RELEASE_COMPARE_BASE_DIR:-artifacts/funding-release-base}}"
CANDIDATE_DIR="${2:-${FUNDING_RELEASE_COMPARE_CANDIDATE_DIR:-artifacts/funding-release}}"
COMPARE_FORMAT="${FUNDING_RELEASE_COMPARE_FORMAT:-markdown}"
REQUIRE_ALIGNED="${FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED:-0}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$COMPARE_FORMAT" in
  text|json|markdown) ;;
  *)
    printf 'FUNDING_RELEASE_COMPARE_FORMAT must be text, json or markdown.\n' >&2
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

require_bool "FUNDING_RELEASE_COMPARE_REQUIRE_ALIGNED" "$REQUIRE_ALIGNED"

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release evidence compare.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$BASE_DIR" "$CANDIDATE_DIR" "$COMPARE_FORMAT" "$REQUIRE_ALIGNED" <<'PY'
import json
import sys
from pathlib import Path

base_dir = Path(sys.argv[1])
candidate_dir = Path(sys.argv[2])
output_format = sys.argv[3]
require_aligned = sys.argv[4] == "1"

errors = []
warnings = []

json_artifacts = [
    ("verify", "funding-release-verify.json", True, "funding_release_evidence_verify_v0", "verification_version"),
    ("notes", "funding-release-notes.json", False, "funding_release_evidence_notes_v0", "notes_version"),
    ("index", "funding-release-index.json", False, "funding_release_evidence_index_v0", "index_version"),
    ("audit", "funding-release-audit.json", False, "funding_release_evidence_audit_v0", "audit_version"),
    ("review", "funding-release-review.json", False, "funding_release_bundle_review_v0", "review_version"),
    ("manifest", "funding-release-manifest.json", False, "funding_release_ci_bundle_v0", "manifest_version"),
    ("report", "funding-release-report.json", False, "funding_release_report_v0", "report_version"),
    ("validation", "funding-release-validation.json", False, None, None),
    ("bundle_validation", "funding-release-bundle-validation.json", False, None, None),
]

markdown_artifacts = [
    "funding-release-index.md",
    "funding-release-verify.md",
    "funding-release-notes.md",
    "funding-release-audit.md",
    "funding-release-summary.md",
    "funding-release-handoff.md",
]

summary_fields = [
    ("verification_status", "verify", "verification_status", True),
    ("blocking_mode", "verify", "blocking_mode", True),
    ("evidence_status", "verify", "evidence_status", True),
    ("release_notes_ready", "verify", "release_notes_ready", True),
    ("debug_review_ready", "verify", "debug_review_ready", True),
    ("review_ready", "verify", "review_ready", True),
    ("review_status", "verify", "review_status", True),
    ("release_gate_status", "verify", "release_gate_status", True),
    ("readiness_gate_status", "verify", "readiness_gate_status", False),
    ("compare_gate_status", "verify", "compare_gate_status", False),
    ("report_exit_code", "verify", "report_exit_code", True),
    ("bundle_exit_code", "verify", "bundle_exit_code", True),
    ("validation_status", "verify", "validation_status", False),
    ("bundle_validation_status", "verify", "bundle_validation_status", False),
    ("notes_status", "notes", "notes_status", False),
    ("notes_mode", "notes", "notes_mode", False),
    ("index_status", "index", "index_status", False),
    ("audit_status", "audit", "audit_status", False),
]

list_fields = [
    ("required_blocking_ids", "verify", "required_blocking_ids", True),
    ("optional_blocking_ids", "verify", "optional_blocking_ids", False),
]

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

def as_dict(value):
    return value if isinstance(value, dict) else {}

def as_list(value):
    return value if isinstance(value, list) else []

def normalized_list(value):
    return sorted(str(item) for item in as_list(value))

def text_value(value):
    if value is None or value == "":
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "none"
    return str(value)

def inline_code(value):
    return f"`{text_value(value).replace('`', chr(39))}`"

def markdown_cell(value):
    return text_value(value).replace("|", "\\|").replace("\n", " ")

def read_json_bundle(bundle_dir, label):
    artifacts = {}
    parsed = {}
    if not bundle_dir.exists():
        add_error(f"{label} bundle directory does not exist: {bundle_dir}")
        return {"bundle_dir": str(bundle_dir), "artifacts": artifacts, "parsed": parsed}
    if not bundle_dir.is_dir():
        add_error(f"{label} bundle path is not a directory: {bundle_dir}")
        return {"bundle_dir": str(bundle_dir), "artifacts": artifacts, "parsed": parsed}

    for artifact_id, filename, required, expected_version, version_field in json_artifacts:
        path = bundle_dir / filename
        info = {
            "id": artifact_id,
            "filename": filename,
            "path": str(path),
            "required": required,
            "exists": path.is_file(),
            "json_valid": None,
            "version_valid": None,
        }
        artifacts[artifact_id] = info
        if not path.is_file():
            if required:
                add_error(f"{label}: missing required artifact {filename}")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            info["json_valid"] = False
            if required:
                add_error(f"{label}: {filename} is not valid JSON: {exc}")
            else:
                add_warning(f"{label}: optional {filename} is not valid JSON: {exc}")
            continue
        if not isinstance(value, dict):
            info["json_valid"] = False
            if required:
                add_error(f"{label}: {filename} must be a JSON object")
            else:
                add_warning(f"{label}: optional {filename} must be a JSON object")
            continue
        info["json_valid"] = True
        if expected_version and version_field:
            info["version_valid"] = value.get(version_field) == expected_version
            if not info["version_valid"]:
                message = f"{label}: {filename} {version_field} must be {expected_version}, got {value.get(version_field)}"
                if required:
                    add_error(message)
                else:
                    add_warning(message)
        parsed[artifact_id] = value

    for filename in markdown_artifacts:
        artifact_id = filename.replace("-", "_").replace(".", "_")
        path = bundle_dir / filename
        artifacts[artifact_id] = {
            "id": artifact_id,
            "filename": filename,
            "path": str(path),
            "required": False,
            "exists": path.is_file(),
            "json_valid": None,
            "version_valid": None,
        }

    return {"bundle_dir": str(bundle_dir), "artifacts": artifacts, "parsed": parsed}

def summary_value(bundle, artifact_id, field):
    artifact = as_dict(bundle["parsed"].get(artifact_id))
    return artifact.get(field)

def bundle_summary(bundle):
    verify = as_dict(bundle["parsed"].get("verify"))
    notes = as_dict(bundle["parsed"].get("notes"))
    return {
        "bundle_dir": bundle["bundle_dir"],
        "verification_status": verify.get("verification_status"),
        "blocking_mode": verify.get("blocking_mode"),
        "evidence_status": verify.get("evidence_status"),
        "release_notes_ready": verify.get("release_notes_ready"),
        "debug_review_ready": verify.get("debug_review_ready"),
        "review_ready": verify.get("review_ready"),
        "review_status": verify.get("review_status"),
        "release_gate_status": verify.get("release_gate_status"),
        "readiness_gate_status": verify.get("readiness_gate_status"),
        "compare_gate_status": verify.get("compare_gate_status"),
        "report_exit_code": verify.get("report_exit_code"),
        "bundle_exit_code": verify.get("bundle_exit_code"),
        "validation_status": verify.get("validation_status"),
        "bundle_validation_status": verify.get("bundle_validation_status"),
        "required_blocking_ids": normalized_list(verify.get("required_blocking_ids")),
        "optional_blocking_ids": normalized_list(verify.get("optional_blocking_ids")),
        "notes_status": notes.get("notes_status"),
        "notes_mode": notes.get("notes_mode"),
        "recommended_next_action": notes.get("recommended_next_action") or verify.get("recommended_next_action"),
    }

base = read_json_bundle(base_dir, "base")
candidate = read_json_bundle(candidate_dir, "candidate")
diffs = []

def add_diff(diff_id, base_value, candidate_value, required, detail):
    diffs.append({
        "id": diff_id,
        "required": required,
        "base": base_value,
        "candidate": candidate_value,
        "detail": detail,
    })

if not errors:
    for field_id, artifact_id, field_name, required in summary_fields:
        base_value = summary_value(base, artifact_id, field_name)
        candidate_value = summary_value(candidate, artifact_id, field_name)
        if base_value != candidate_value:
            add_diff(field_id, base_value, candidate_value, required, f"{artifact_id}.{field_name} changed")

    for field_id, artifact_id, field_name, required in list_fields:
        base_value = normalized_list(summary_value(base, artifact_id, field_name))
        candidate_value = normalized_list(summary_value(candidate, artifact_id, field_name))
        if base_value != candidate_value:
            add_diff(field_id, base_value, candidate_value, required, f"{artifact_id}.{field_name} changed")

    artifact_ids = sorted(set(base["artifacts"]) | set(candidate["artifacts"]))
    for artifact_id in artifact_ids:
        base_artifact = as_dict(base["artifacts"].get(artifact_id))
        candidate_artifact = as_dict(candidate["artifacts"].get(artifact_id))
        base_exists = bool(base_artifact.get("exists"))
        candidate_exists = bool(candidate_artifact.get("exists"))
        if base_exists != candidate_exists:
            filename = base_artifact.get("filename") or candidate_artifact.get("filename") or artifact_id
            add_diff(
                f"artifact_presence:{filename}",
                base_exists,
                candidate_exists,
                False,
                f"{filename} presence changed",
            )

base_summary = bundle_summary(base)
candidate_summary = bundle_summary(candidate)
blocking_diff_count = sum(1 for diff in diffs if diff["required"])

if errors:
    compare_status = "failed"
    comparison_mode = "artifact_integrity_failed"
    exit_code = 1
elif diffs:
    compare_status = "drift_detected"
    comparison_mode = "blocking_drift" if blocking_diff_count else "non_blocking_drift"
    exit_code = 2 if require_aligned else 0
else:
    compare_status = "aligned"
    comparison_mode = "aligned"
    exit_code = 0

if compare_status == "failed":
    recommended_next_action = "Regenerate or verify both Funding release evidence bundles before comparing"
elif compare_status == "aligned":
    recommended_next_action = "Use candidate Funding release evidence bundle with the same release readiness posture as base"
elif blocking_diff_count:
    recommended_next_action = "Review blocking Funding release evidence drift before release handoff"
else:
    recommended_next_action = "Inspect non-blocking Funding release evidence drift before attaching artifacts"

artifact_presence = []
for artifact_id in sorted(set(base["artifacts"]) | set(candidate["artifacts"])):
    base_artifact = as_dict(base["artifacts"].get(artifact_id))
    candidate_artifact = as_dict(candidate["artifacts"].get(artifact_id))
    artifact_presence.append({
        "id": artifact_id,
        "filename": base_artifact.get("filename") or candidate_artifact.get("filename") or artifact_id,
        "base_exists": bool(base_artifact.get("exists")),
        "candidate_exists": bool(candidate_artifact.get("exists")),
    })

compare = {
    "compare_version": "funding_release_evidence_compare_v0",
    "compare_status": compare_status,
    "comparison_mode": comparison_mode,
    "exit_code": exit_code,
    "require_aligned": require_aligned,
    "base_dir": str(base_dir),
    "candidate_dir": str(candidate_dir),
    "base_summary": base_summary,
    "candidate_summary": candidate_summary,
    "diff_count": len(diffs),
    "blocking_diff_count": blocking_diff_count,
    "diffs": diffs,
    "artifact_presence": artifact_presence,
    "recommended_next_action": recommended_next_action,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(compare, ensure_ascii=False, indent=2))
elif output_format == "markdown":
    print("### Funding Release Evidence Compare")
    print("")
    print(f"- compare_status: {inline_code(compare_status)}")
    print(f"- comparison_mode: {inline_code(comparison_mode)}")
    print(f"- diff_count: {inline_code(len(diffs))}")
    print(f"- blocking_diff_count: {inline_code(blocking_diff_count)}")
    print(f"- require_aligned: {inline_code(require_aligned)}")
    print(f"- recommended_next_action: {inline_code(recommended_next_action)}")
    print("")
    print("#### Bundle Summary")
    print("| Field | Base | Candidate |")
    print("|---|---|---|")
    for field in (
        "verification_status",
        "evidence_status",
        "release_notes_ready",
        "debug_review_ready",
        "review_status",
        "release_gate_status",
        "required_blocking_ids",
        "notes_status",
        "notes_mode",
    ):
        print(
            f"| {markdown_cell(field)} "
            f"| {markdown_cell(base_summary.get(field))} "
            f"| {markdown_cell(candidate_summary.get(field))} |"
        )
    print("")
    print("#### Diffs")
    if diffs:
        print("| Diff | Required | Base | Candidate | Detail |")
        print("|---|---:|---|---|---|")
        for diff in diffs:
            print(
                f"| {markdown_cell(diff['id'])} "
                f"| {markdown_cell(diff['required'])} "
                f"| {markdown_cell(diff['base'])} "
                f"| {markdown_cell(diff['candidate'])} "
                f"| {markdown_cell(diff['detail'])} |"
            )
    else:
        print("- none")
    print("")
    print("#### Artifact Presence")
    print("| Artifact | Base | Candidate |")
    print("|---|---:|---:|")
    for row in artifact_presence:
        print(
            f"| {markdown_cell(row['filename'])} "
            f"| {markdown_cell(row['base_exists'])} "
            f"| {markdown_cell(row['candidate_exists'])} |"
        )
    if errors:
        print("")
        print("#### Compare Errors")
        for error in errors:
            print(f"- {inline_code(error)}")
    if warnings:
        print("")
        print("#### Compare Warnings")
        for warning in warnings:
            print(f"- {inline_code(warning)}")
else:
    print("Funding release evidence compare")
    print(f"- base_dir: {base_dir}")
    print(f"- candidate_dir: {candidate_dir}")
    print(f"- compare_status: {compare_status}")
    print(f"- comparison_mode: {comparison_mode}")
    print(f"- diff_count: {len(diffs)}")
    print(f"- blocking_diff_count: {blocking_diff_count}")
    print(f"- recommended_next_action: {recommended_next_action}")
    if diffs:
        print("- diffs:")
        for diff in diffs:
            print(
                f"  - {diff['id']}: required={text_value(diff['required'])}"
                f" base={text_value(diff['base'])}"
                f" candidate={text_value(diff['candidate'])}"
            )
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
