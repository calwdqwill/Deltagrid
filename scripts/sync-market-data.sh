#!/usr/bin/env sh
set -eu

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"

cd "$(dirname "$0")/.."

if [ -n "$COMPOSE_PROJECT_NAME" ]; then
  COMPOSE_PROJECT_ARGS="-p $COMPOSE_PROJECT_NAME"
else
  COMPOSE_PROJECT_ARGS=""
fi

# shellcheck disable=SC2086
ENV_FILE="$ENV_FILE" docker compose $COMPOSE_PROJECT_ARGS --env-file "$ENV_FILE" -f "$COMPOSE_FILE" exec -T backend \
  python -m app.adapters.data.sync_market_data \
  --include-funding \
  --include-open-interest \
  --include-long-short \
  --include-liquidations \
  --include-coinglass \
  --include-coingecko-basis \
  "$@"
