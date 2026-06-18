#!/usr/bin/env sh
set -eu

BRANCH="${BRANCH:?set BRANCH}"
REMOTE="${REMOTE:-origin}"
ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"

cd "$(dirname "$0")/.."

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file is missing: $ENV_FILE" >&2
  exit 1
fi

read_env_value() {
  key="$1"
  sed -n "s/^${key}=//p" "$ENV_FILE" | tail -n 1
}

compose() {
  if [ -n "$COMPOSE_PROJECT_NAME" ]; then
    ENV_FILE="$ENV_FILE" docker compose -p "$COMPOSE_PROJECT_NAME" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  else
    ENV_FILE="$ENV_FILE" docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  fi
}

wait_for_service() {
  service="$1"
  timeout_seconds="${2:-180}"
  elapsed_seconds=0

  printf 'Waiting for %s to become healthy ...\n' "$service"

  while [ "$elapsed_seconds" -lt "$timeout_seconds" ]; do
    container_id="$(compose ps -q "$service")"

    if [ -n "$container_id" ]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"

      if [ "$status" = "healthy" ]; then
        printf '%s ... healthy\n' "$service"
        return 0
      fi
    fi

    sleep 3
    elapsed_seconds=$((elapsed_seconds + 3))
  done

  printf '%s did not become healthy within %s seconds.\n' "$service" "$timeout_seconds"
  compose logs --tail=80 "$service" || true
  exit 1
}

backend_port="${BACKEND_HOST_PORT:-$(read_env_value BACKEND_HOST_PORT)}"
frontend_port="${FRONTEND_HOST_PORT:-$(read_env_value FRONTEND_HOST_PORT)}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${backend_port:-8000}}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:${frontend_port:-3001}}"

git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

compose config >/dev/null

if [ -z "${BACKUP_BEFORE_DEPLOY:-}" ]; then
  if [ "$BRANCH" = "main" ]; then
    BACKUP_BEFORE_DEPLOY=1
  else
    BACKUP_BEFORE_DEPLOY=0
  fi
fi

if [ "$BACKUP_BEFORE_DEPLOY" = "1" ]; then
  backup_dir="${BACKUP_DIR:-backups/deploy}"
  backup_prefix="${BACKUP_PREFIX:-deltagrid-${BRANCH}}"
  printf 'Creating PostgreSQL backup before deploy ...\n'
  ENV_FILE="$ENV_FILE" \
    COMPOSE_FILE="$COMPOSE_FILE" \
    COMPOSE_PROJECT_NAME="$COMPOSE_PROJECT_NAME" \
    BACKUP_DIR="$backup_dir" \
    BACKUP_PREFIX="$backup_prefix" \
    sh scripts/backup-postgres.sh
fi

# Build before stopping running services; then recreate app containers explicitly
# to avoid Docker Compose rename conflicts during backend/frontend deploys.
compose build backend frontend
compose rm -sf backend frontend
compose up -d --no-build backend frontend

wait_for_service postgres 120
wait_for_service backend 180
wait_for_service frontend 180

BASE_URL="$BASE_URL" FRONTEND_URL="$FRONTEND_URL" sh scripts/server-smoke.sh
