#!/usr/bin/env sh
set -eu

MANIFEST_FILE="${1:-${FUNDING_RELEASE_BUNDLE_REVIEW_FILE:-artifacts/funding-release/funding-release-manifest.json}}"
REVIEW_FORMAT="${FUNDING_RELEASE_BUNDLE_REVIEW_FORMAT:-text}"
BUNDLE_VALIDATION_FILE="${FUNDING_RELEASE_BUNDLE_REVIEW_VALIDATION_FILE:-}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

case "$REVIEW_FORMAT" in
  text|json) ;;
  *)
    printf 'FUNDING_RELEASE_BUNDLE_REVIEW_FORMAT must be text or json.\n' >&2
    exit 1
    ;;
esac

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    printf 'python3/python is required for Funding release bundle review.\n' >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$MANIFEST_FILE" "$REVIEW_FORMAT" "$BUNDLE_VALIDATION_FILE" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
output_format = sys.argv[2]
bundle_validation_path_raw = sys.argv[3]

def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return {"status": "parse_error", "artifact": str(path)}
    return value if isinstance(value, dict) else {"status": "invalid_shape", "artifact": str(path)}

def load_manifest(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Funding release bundle manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Funding release bundle manifest is not valid JSON: {exc}")
    if not isinstance(value, dict):
        raise SystemExit("Funding release bundle manifest must be a JSON object")
    return value

def default_bundle_validation_path():
    if bundle_validation_path_raw:
        return Path(bundle_validation_path_raw)
    return manifest_path.parent / "funding-release-bundle-validation.json"

def file_review(files, key):
    entry = files.get(key) if isinstance(files, dict) else {}
    if not isinstance(entry, dict):
        return {
            "configured": False,
            "exists": False,
            "json_valid": None,
            "size_bytes": None,
            "sha256": None,
        }
    return {
        "configured": entry.get("configured") is True,
        "exists": entry.get("exists") is True,
        "json_valid": entry.get("json_valid"),
        "size_bytes": entry.get("size_bytes"),
        "sha256": entry.get("sha256"),
    }

def short_sha(value):
    if not isinstance(value, str) or not value:
        return None
    return value[:12]

manifest = load_manifest(manifest_path)
bundle_validation_path = default_bundle_validation_path()
bundle_validation = read_json(bundle_validation_path)

artifact_status = manifest.get("artifact_status") if isinstance(manifest.get("artifact_status"), dict) else {}
report_summary = manifest.get("report_summary") if isinstance(manifest.get("report_summary"), dict) else {}
run_context = manifest.get("run_context") if isinstance(manifest.get("run_context"), dict) else {}
files = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
ci_context = run_context.get("ci") if isinstance(run_context.get("ci"), dict) else {}

bundle_validation_status = None
bundle_validation_error_count = None
if isinstance(bundle_validation, dict):
    bundle_validation_status = bundle_validation.get("status")
    bundle_validation_error_count = bundle_validation.get("error_count")

required_blocking_ids = report_summary.get("required_blocking_ids")
if not isinstance(required_blocking_ids, list):
    required_blocking_ids = report_summary.get("blocking_ids") if isinstance(report_summary.get("blocking_ids"), list) else []
optional_blocking_ids = report_summary.get("optional_blocking_ids")
if not isinstance(optional_blocking_ids, list):
    optional_blocking_ids = []

release_gate_status = artifact_status.get("release_gate_status")
validation_status = artifact_status.get("validation_status")
exit_reason = artifact_status.get("exit_reason")
bundle_exit_code = manifest.get("bundle_exit_code")
report_exit_code = manifest.get("report_exit_code")
validation_exit_code = manifest.get("validation_exit_code")

if bundle_validation_status in {None, "parse_error", "invalid_shape"}:
    review_status = "incomplete"
elif bundle_validation_status != "passed":
    review_status = "invalid_bundle"
elif release_gate_status == "passed":
    review_status = "passed"
elif release_gate_status == "blocked":
    review_status = "blocked"
elif release_gate_status == "failed":
    review_status = "failed"
else:
    review_status = "unknown"

if review_status == "invalid_bundle":
    recommended_next_action = "Fix evidence bundle integrity before using this artifact"
elif review_status == "incomplete":
    recommended_next_action = "Run bundle validation or inspect missing bundle validation artifact"
elif validation_status == "failed" or validation_exit_code not in (0, None):
    recommended_next_action = "Fix compact report validation errors before release review"
elif release_gate_status == "failed":
    recommended_next_action = "Inspect underlying Funding smoke failure"
elif required_blocking_ids:
    recommended_next_action = report_summary.get("first_blocking_action") or "Resolve required Funding release blockers"
elif release_gate_status == "passed":
    recommended_next_action = "Attach evidence bundle to release notes or runbook"
elif optional_blocking_ids:
    recommended_next_action = report_summary.get("first_optional_action") or "Review optional Funding release blockers"
else:
    recommended_next_action = "Inspect manifest and compact report"

file_summary = {
    "report": file_review(files, "report"),
    "stdout": file_review(files, "stdout"),
    "validation": file_review(files, "validation"),
    "manifest": file_review(files, "manifest"),
}

review = {
    "review_version": "funding_release_bundle_review_v0",
    "review_status": review_status,
    "recommended_next_action": recommended_next_action,
    "artifact": str(manifest_path),
    "bundle_validation_artifact": str(bundle_validation_path),
    "bundle_validation_status": bundle_validation_status,
    "bundle_validation_error_count": bundle_validation_error_count,
    "manifest_version": manifest.get("manifest_version"),
    "generated_at": manifest.get("generated_at"),
    "bundle_exit_code": bundle_exit_code,
    "report_exit_code": report_exit_code,
    "validation_exit_code": validation_exit_code,
    "release_gate_status": release_gate_status,
    "exit_reason": exit_reason,
    "validation_status": validation_status,
    "readiness_gate_status": report_summary.get("readiness_gate_status"),
    "compare_gate_status": report_summary.get("compare_gate_status"),
    "required_blocking_ids": required_blocking_ids,
    "optional_blocking_ids": optional_blocking_ids,
    "first_blocking_action": report_summary.get("first_blocking_action"),
    "first_optional_action": report_summary.get("first_optional_action"),
    "run_context": {
        "report_profile": run_context.get("report_profile"),
        "ci_provider": ci_context.get("provider"),
        "base_url": run_context.get("base_url"),
        "frontend_url": run_context.get("frontend_url"),
        "compare_base_url": run_context.get("compare_base_url"),
        "run_frontend_check": run_context.get("run_frontend_check"),
        "min_total_rows": run_context.get("min_total_rows"),
    },
    "files": file_summary,
}

if output_format == "json":
    print(json.dumps(review, ensure_ascii=False, indent=2))
else:
    report_file = file_summary["report"]
    print("Funding release bundle review")
    print(f"- artifact: {manifest_path}")
    print(f"- review_status: {review_status}")
    print(f"- recommended_next_action: {recommended_next_action}")
    print(f"- bundle_exit_code: {bundle_exit_code}")
    print(f"- report_exit_code: {report_exit_code}")
    print(f"- validation_exit_code: {validation_exit_code}")
    print(f"- bundle_validation_status: {bundle_validation_status or 'missing'}")
    print(f"- release_gate_status: {release_gate_status}")
    print(f"- exit_reason: {exit_reason}")
    print(f"- readiness_gate_status: {report_summary.get('readiness_gate_status')}")
    print(f"- compare_gate_status: {report_summary.get('compare_gate_status')}")
    print(f"- required_blocking_ids: {', '.join(required_blocking_ids) if required_blocking_ids else 'none'}")
    print(f"- optional_blocking_ids: {', '.join(optional_blocking_ids) if optional_blocking_ids else 'none'}")
    print(f"- first_blocking_action: {report_summary.get('first_blocking_action') or 'none'}")
    print(f"- first_optional_action: {report_summary.get('first_optional_action') or 'none'}")
    print(f"- report_sha256: {short_sha(report_file.get('sha256')) or 'none'}")
PY
