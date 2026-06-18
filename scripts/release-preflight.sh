#!/usr/bin/env sh
set -eu

EXPECTED_VERSION="${1:-${EXPECTED_VERSION:-}}"
EXPECTED_BRANCH="${RELEASE_BRANCH:-}"
RELEASE_TARGET="${RELEASE_TARGET:-}"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"

cd "$(dirname "$0")/.."

fail() {
  printf 'release preflight failed: %s\n' "$1" >&2
  exit 1
}

read_trimmed_file() {
  tr -d '\r\n' < "$1"
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"
}

require_semver_target() {
  value="$1"
  printf '%s\n' "$value" | grep -Eq '^[0-9]+[.][0-9]+[.][0-9]+(-rc[.][0-9]+)?$' ||
    fail "release target must look like SemVer or rc target: $value"
}

require_command git

if command -v node >/dev/null 2>&1; then
  package_version="$(node -e "console.log(require('./frontend/package.json').version)")"
  lock_version="$(node -e "console.log(require('./frontend/package-lock.json').packages[''].version)")"
elif command -v python3 >/dev/null 2>&1; then
  package_version="$(python3 -c "import json; print(json.load(open('frontend/package.json', encoding='utf-8'))['version'])")"
  lock_version="$(python3 -c "import json; print(json.load(open('frontend/package-lock.json', encoding='utf-8'))['packages']['']['version'])")"
elif command -v python >/dev/null 2>&1; then
  package_version="$(python -c "import json; print(json.load(open('frontend/package.json', encoding='utf-8'))['version'])")"
  lock_version="$(python -c "import json; print(json.load(open('frontend/package-lock.json', encoding='utf-8'))['packages']['']['version'])")"
else
  fail "missing command: node, python3 or python"
fi

root_version="$(read_trimmed_file VERSION)"

if [ -n "$RELEASE_TARGET" ]; then
  require_semver_target "$RELEASE_TARGET"
fi

if [ -n "$EXPECTED_VERSION" ] && [ "$root_version" != "$EXPECTED_VERSION" ]; then
  fail "VERSION is $root_version, expected $EXPECTED_VERSION"
fi

if [ "$package_version" != "$root_version" ]; then
  fail "frontend/package.json version is $package_version, expected $root_version"
fi

if [ "$lock_version" != "$root_version" ]; then
  fail "frontend/package-lock.json root package version is $lock_version, expected $root_version"
fi

if [ -n "$EXPECTED_BRANCH" ]; then
  current_branch="$(git branch --show-current)"
  if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
    fail "current branch is $current_branch, expected $EXPECTED_BRANCH"
  fi
fi

if [ "$ALLOW_DIRTY" != "1" ] && [ -n "$(git status --porcelain)" ]; then
  fail "working tree is dirty; commit or stash changes before release"
fi

printf 'DeltaGrid release preflight passed: version=%s' "$root_version"
if [ -n "$RELEASE_TARGET" ]; then
  printf ' target=%s' "$RELEASE_TARGET"
fi
if [ -n "$EXPECTED_BRANCH" ]; then
  printf ' branch=%s' "$EXPECTED_BRANCH"
fi
printf '\n'
