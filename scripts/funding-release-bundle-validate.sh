#!/usr/bin/env sh
set -eu

MANIFEST_FILE="${1:-${FUNDING_RELEASE_BUNDLE_VALIDATE_FILE:-artifacts/funding-release/funding-release-manifest.json}}"
VALIDATE_FORMAT="${FUNDING_RELEASE_BUNDLE_VALIDATE_FORMAT:-text}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$VALIDATE_FORMAT" in
  text|json) ;;
  *)
    printf 'FUNDING_RELEASE_BUNDLE_VALIDATE_FORMAT must be text or json.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release bundle validation.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$MANIFEST_FILE" "$VALIDATE_FORMAT" <<'PY'
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

manifest_path = Path(sys.argv[1])
output_format = sys.argv[2]
errors = []
warnings = []

def add_error(message):
    errors.append(message)

def add_warning(message):
    warnings.append(message)

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

def require_bool_value(parent, key, path):
    value = parent.get(key) if isinstance(parent, dict) else None
    if not isinstance(value, bool):
        add_error(f"{path}.{key} must be boolean")
        return None
    return value

def require_enum(parent, key, allowed, path):
    value = require_str(parent, key, path)
    if value and value not in allowed:
        add_error(f"{path}.{key} has unsupported value {value!r}")
    return value

def load_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Funding release bundle manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Funding release bundle manifest is not valid JSON: {exc}")

def candidate_paths(raw_path):
    if raw_path is None:
        return []
    path = Path(raw_path)
    if path.is_absolute():
        return [path]
    candidates = [
        manifest_path.parent / path.name,
        manifest_path.parent / path,
        path,
    ]
    unique = []
    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique

def resolve_existing_path(raw_path):
    for candidate in candidate_paths(raw_path):
        if candidate.is_file():
            return candidate
    candidates = candidate_paths(raw_path)
    return candidates[0] if candidates else None

def actual_file_info(path):
    data = path.read_bytes()
    info = {
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    try:
        json.loads(data.decode("utf-8"))
        info["json_valid"] = True
    except Exception:
        info["json_valid"] = False
    return info

def validate_file_entry(files, key, required):
    entry = require_dict(files, key, "files")
    configured = require_bool_value(entry, "configured", f"files.{key}")
    exists = require_bool_value(entry, "exists", f"files.{key}")
    raw_path = entry.get("path")
    if configured is False and raw_path is not None:
        add_error(f"files.{key}.path must be null when file is not configured")
    if configured is True and not isinstance(raw_path, str):
        add_error(f"files.{key}.path must be string when configured")
        raw_path = None
    if required and configured is not True:
        add_error(f"files.{key}.configured must be true")
    if required and exists is not True:
        add_error(f"files.{key}.exists must be true")
    actual_path = resolve_existing_path(raw_path) if configured else None
    actual_exists = actual_path.is_file() if actual_path else False
    if exists is True and not actual_exists:
        add_error(f"files.{key}.exists is true but file is missing")
    if exists is False and actual_exists and key != "manifest":
        add_error(f"files.{key}.exists is false but file exists")
    if not actual_exists:
        return entry
    actual = actual_file_info(actual_path)
    for field in ("size_bytes", "sha256", "json_valid"):
        if field in entry and entry.get(field) != actual[field]:
            add_error(f"files.{key}.{field} does not match actual file")
    return entry

manifest = load_json_file(manifest_path)
if not isinstance(manifest, dict):
    raise SystemExit("Funding release bundle manifest must be a JSON object")

required_top_fields = [
    "manifest_version",
    "generated_at",
    "bundle_exit_code",
    "report_exit_code",
    "validation_exit_code",
    "validation_enabled",
    "manifest_enabled",
    "artifact_status",
    "report_summary",
    "run_context",
    "files",
]
for field in required_top_fields:
    if field not in manifest:
        add_error(f"missing top-level field: {field}")

manifest_version = require_str(manifest, "manifest_version", "manifest")
if manifest_version != "funding_release_ci_bundle_v0":
    add_error("manifest.manifest_version must be funding_release_ci_bundle_v0")

generated_at = require_str(manifest, "generated_at", "manifest")
if generated_at:
    try:
        datetime.fromisoformat(generated_at)
    except ValueError:
        add_error("manifest.generated_at must be ISO-8601 datetime")

bundle_exit_code = require_int(manifest, "bundle_exit_code", "manifest")
report_exit_code = require_int(manifest, "report_exit_code", "manifest")
validation_exit_code = require_int(manifest, "validation_exit_code", "manifest")
validation_enabled = require_bool_value(manifest, "validation_enabled", "manifest")
manifest_enabled = require_bool_value(manifest, "manifest_enabled", "manifest")
artifact_status = require_dict(manifest, "artifact_status", "manifest")
report_summary = require_dict(manifest, "report_summary", "manifest")
run_context = require_dict(manifest, "run_context", "manifest")
files = require_dict(manifest, "files", "manifest")

if manifest_enabled is not True:
    add_error("manifest.manifest_enabled must be true for a written bundle manifest")

if bundle_exit_code is not None and report_exit_code is not None and validation_exit_code is not None:
    expected_bundle_exit = validation_exit_code if validation_exit_code != 0 else report_exit_code
    if bundle_exit_code != expected_bundle_exit:
        add_error("manifest.bundle_exit_code must equal validation_exit_code when validation fails, otherwise report_exit_code")

release_gate_status = require_enum(
    artifact_status,
    "release_gate_status",
    {"passed", "blocked", "failed"},
    "artifact_status",
)
exit_reason = require_enum(
    artifact_status,
    "exit_reason",
    {"passed", "smoke_failed", "readiness_not_ready", "compare_not_aligned"},
    "artifact_status",
)
validation_status = artifact_status.get("validation_status")
validation_error_count = artifact_status.get("validation_error_count")
validation_warning_count = artifact_status.get("validation_warning_count")

if validation_enabled:
    if validation_status not in {"passed", "failed"}:
        add_error("artifact_status.validation_status must be passed or failed when validation is enabled")
    if not isinstance(validation_error_count, int):
        add_error("artifact_status.validation_error_count must be integer when validation is enabled")
    if not isinstance(validation_warning_count, int):
        add_error("artifact_status.validation_warning_count must be integer when validation is enabled")
else:
    if validation_status is not None:
        add_warning("artifact_status.validation_status is present while validation is disabled")

if validation_exit_code == 0 and validation_enabled and validation_status != "passed":
    add_error("validation_exit_code=0 requires artifact_status.validation_status=passed")
if validation_exit_code and validation_enabled and validation_status != "failed":
    add_error("non-zero validation_exit_code requires artifact_status.validation_status=failed")

if report_exit_code == 0 and exit_reason != "passed":
    add_error("report_exit_code=0 requires exit_reason=passed")
if report_exit_code and exit_reason == "passed":
    add_error("non-zero report_exit_code must not use exit_reason=passed")
if exit_reason == "passed" and release_gate_status != "passed":
    add_error("exit_reason=passed requires release_gate_status=passed")
if exit_reason == "smoke_failed" and release_gate_status != "failed":
    add_error("exit_reason=smoke_failed requires release_gate_status=failed")
if exit_reason in {"readiness_not_ready", "compare_not_aligned"} and release_gate_status != "blocked":
    add_error("report-level gate failures require release_gate_status=blocked")

require_str(report_summary, "report_version", "report_summary")
require_str(report_summary, "contract", "report_summary")
require_str(report_summary, "readiness_gate_status", "report_summary")
require_str(report_summary, "readiness_status", "report_summary")
require_str(report_summary, "compare_gate_status", "report_summary")
require_str(report_summary, "compare_status", "report_summary")
blocking_ids = require_list(report_summary, "blocking_ids", "report_summary")
required_blocking_ids = require_list(report_summary, "required_blocking_ids", "report_summary")
optional_blocking_ids = require_list(report_summary, "optional_blocking_ids", "report_summary")
first_blocking_action = report_summary.get("first_blocking_action")
first_optional_action = report_summary.get("first_optional_action")

if blocking_ids != required_blocking_ids:
    add_error("report_summary.blocking_ids must match required_blocking_ids")
if required_blocking_ids and not isinstance(first_blocking_action, str):
    add_error("report_summary.first_blocking_action must be string when required blockers exist")
if not required_blocking_ids and first_blocking_action is not None:
    add_error("report_summary.first_blocking_action must be null without required blockers")
if optional_blocking_ids and not required_blocking_ids and not isinstance(first_optional_action, str):
    add_error("report_summary.first_optional_action must be string when only optional blockers exist")
if required_blocking_ids and first_optional_action is not None:
    add_error("report_summary.first_optional_action must be null when required blockers exist")
if release_gate_status == "passed" and required_blocking_ids:
    add_error("passed release_gate_status must not have required blockers")
if release_gate_status == "blocked" and not required_blocking_ids:
    add_error("blocked release_gate_status requires required blockers")

for field in ("report_profile", "report_format", "ci", "base_url", "frontend_url"):
    if field not in run_context:
        add_error(f"run_context missing field: {field}")
if isinstance(run_context.get("ci"), dict):
    ci_provider = run_context["ci"].get("provider")
    if ci_provider not in {"local", "generic_ci", "github_actions"}:
        add_error("run_context.ci.provider has unsupported value")

validate_file_entry(files, "report", required=True)
validate_file_entry(files, "stdout", required=False)
validate_file_entry(files, "validation", required=validation_enabled is True)
manifest_file_entry = validate_file_entry(files, "manifest", required=False)
manifest_entry_path = manifest_file_entry.get("path") if isinstance(manifest_file_entry, dict) else None
if manifest_entry_path and Path(manifest_entry_path).name != manifest_path.name:
    add_error("files.manifest.path must reference the validated manifest filename")

result = {
    "status": "failed" if errors else "passed",
    "artifact": str(manifest_path),
    "manifest_version": manifest_version,
    "bundle_exit_code": bundle_exit_code,
    "report_exit_code": report_exit_code,
    "validation_exit_code": validation_exit_code,
    "release_gate_status": release_gate_status,
    "validation_status": validation_status,
    "error_count": len(errors),
    "warning_count": len(warnings),
    "errors": errors,
    "warnings": warnings,
}

if output_format == "json":
    print(json.dumps(result, ensure_ascii=False, indent=2))
else:
    print("Funding release bundle validation")
    print(f"- artifact: {manifest_path}")
    print(f"- status: {result['status']}")
    print(f"- bundle_exit_code: {bundle_exit_code}")
    print(f"- release_gate_status: {release_gate_status}")
    print(f"- validation_status: {validation_status}")
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
