#!/usr/bin/env sh
set -eu

DOMAIN="${DOMAIN:-deltagrid.pro}"
ENV_FILE="${ENV_FILE:-.env.production}"

wait_for_service() {
  service="$1"
  timeout_seconds="${2:-120}"
  elapsed_seconds=0

  printf 'Waiting for %s to become healthy ...\n' "$service"

  while [ "$elapsed_seconds" -lt "$timeout_seconds" ]; do
    container_id="$(docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml ps -q "$service")"

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
  docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml logs --tail=80 "$service" || true
  exit 1
}

if [ ! -f "$ENV_FILE" ]; then
  printf '%s is missing. Generating production env for %s...\n' "$ENV_FILE" "$DOMAIN"
  ENV_FILE="$ENV_FILE" sh scripts/generate-production-env.sh "$DOMAIN"
fi

printf 'Validating production compose config...\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml config >/dev/null

printf 'Building and starting DeltaGrid production stack...\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build

wait_for_service postgres 120
wait_for_service backend 180
wait_for_service frontend 180

printf 'Container status:\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml ps

printf 'Running local smoke-check...\n'
sh scripts/server-smoke.sh

printf 'DeltaGrid production stack is running locally. Configure Nginx/SSL and run domain smoke-check next.\n'
