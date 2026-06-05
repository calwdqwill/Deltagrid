#!/usr/bin/env sh
set -eu

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$(dirname "$0")/.."

docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python -m app.adapters.data.sync_market_data \
  --include-funding \
  --include-open-interest \
  --include-long-short \
  --include-coinglass \
  --include-coingecko-basis \
  "$@"
