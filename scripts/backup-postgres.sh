#!/usr/bin/env sh
set -eu

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-backups}"
BACKUP_PREFIX="${BACKUP_PREFIX:-deltagrid}"
COMPRESS="${COMPRESS:-1}"

cd "$(dirname "$0")/.."

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file is missing: $ENV_FILE" >&2
  exit 1
fi

read_env_value() {
  key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -n 1
}

POSTGRES_DB="${POSTGRES_DB:-$(read_env_value POSTGRES_DB)}"
POSTGRES_USER="${POSTGRES_USER:-$(read_env_value POSTGRES_USER)}"

if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ]; then
  echo "POSTGRES_DB and POSTGRES_USER must be set in $ENV_FILE or environment." >&2
  exit 1
fi

compose() {
  if [ -n "$COMPOSE_PROJECT_NAME" ]; then
    ENV_FILE="$ENV_FILE" docker compose -p "$COMPOSE_PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  else
    ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  fi
}

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

if [ "$COMPRESS" = "1" ]; then
  if ! command -v gzip >/dev/null 2>&1; then
    echo "gzip is not available; rerun with COMPRESS=0 or install gzip." >&2
    exit 1
  fi
  output_path="$BACKUP_DIR/${BACKUP_PREFIX}_${timestamp}.sql.gz"
  compose exec -T "$POSTGRES_SERVICE" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip -c >"$output_path"
  gzip -t "$output_path"
else
  output_path="$BACKUP_DIR/${BACKUP_PREFIX}_${timestamp}.sql"
  compose exec -T "$POSTGRES_SERVICE" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" >"$output_path"
fi

bytes="$(wc -c <"$output_path" | tr -d ' ')"

if [ "$bytes" = "0" ]; then
  echo "Backup is empty: $output_path" >&2
  exit 1
fi

echo "PostgreSQL backup created: $output_path ($bytes bytes)"
