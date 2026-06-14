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

backend_port="${BACKEND_HOST_PORT:-$(read_env_value BACKEND_HOST_PORT)}"
frontend_port="${FRONTEND_HOST_PORT:-$(read_env_value FRONTEND_HOST_PORT)}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${backend_port:-8000}}"
FRONTEND_URL="${FRONTEND_URL:-http://127.0.0.1:${frontend_port:-3001}}"

git fetch "$REMOTE" "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

compose config >/dev/null
compose up -d --build backend frontend

BASE_URL="$BASE_URL" FRONTEND_URL="$FRONTEND_URL" sh scripts/server-smoke.sh
