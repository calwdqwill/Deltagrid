#!/usr/bin/env sh
set -eu

DOMAIN="${DOMAIN:-deltagrid.pro}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [ ! -f "$ENV_FILE" ]; then
  printf '%s is missing. Generating production env for %s...\n' "$ENV_FILE" "$DOMAIN"
  ENV_FILE="$ENV_FILE" sh scripts/generate-production-env.sh "$DOMAIN"
fi

printf 'Validating production compose config...\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml config >/dev/null

printf 'Building and starting DeltaGrid production stack...\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml up -d --build

printf 'Container status:\n'
docker compose --env-file "$ENV_FILE" -f docker-compose.prod.yml ps

printf 'Running local smoke-check...\n'
sh scripts/server-smoke.sh

printf 'DeltaGrid production stack is running locally. Configure Nginx/SSL and run domain smoke-check next.\n'
