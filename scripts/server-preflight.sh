#!/usr/bin/env sh
set -eu

DOMAIN="${DOMAIN:-}"

need_command() {
  name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '%s ... ok\n' "$name"
  else
    printf '%s ... missing\n' "$name"
    return 1
  fi
}

printf 'DeltaGrid server preflight\n'
printf 'Working directory: %s\n' "$(pwd)"

missing=0
for command_name in git docker curl nginx; do
  need_command "$command_name" || missing=1
done

if docker compose version >/dev/null 2>&1; then
  printf 'docker compose ... ok\n'
else
  printf 'docker compose ... missing\n'
  missing=1
fi

if docker info >/dev/null 2>&1; then
  printf 'docker daemon ... ok\n'
else
  printf 'docker daemon ... unavailable\n'
  missing=1
fi

if [ -n "$DOMAIN" ]; then
  printf 'domain lookup (%s) ... ' "$DOMAIN"
  if getent hosts "$DOMAIN" >/dev/null 2>&1; then
    getent hosts "$DOMAIN" | head -n 1
  else
    printf 'failed\n'
    missing=1
  fi
fi

printf 'compose prod config ... '
if ENV_FILE=.env.production.example docker compose --env-file .env.production.example -f docker-compose.prod.yml config >/dev/null 2>&1; then
  printf 'ok\n'
else
  printf 'failed\n'
  missing=1
fi

printf 'ports currently listening:\n'
if command -v ss >/dev/null 2>&1; then
  ss -ltn | grep -E ':(80|443|3000|8000)\b' || true
else
  printf 'ss command unavailable; skipping port list\n'
fi

if [ "$missing" -ne 0 ]; then
  printf 'Preflight failed. Install missing dependencies or fix unavailable services before deploy.\n'
  exit 1
fi

printf 'Preflight passed.\n'
