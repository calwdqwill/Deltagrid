#!/usr/bin/env sh
set -eu

PROJECT_DIR="${PROJECT_DIR:-/opt/deltagrid}"
SCHEDULE="${SCHEDULE:-*/15 * * * *}"
LOG_FILE="${LOG_FILE:-/var/log/deltagrid-market-sync.log}"
SYMBOLS="${SYMBOLS:-BTC,ETH,SOL}"
LOOKBACK_HOURS="${LOOKBACK_HOURS:-2}"
OHLCV_INTERVALS="${OHLCV_INTERVALS:-1m,5m,1h}"
CRON_FILE="${CRON_FILE:-/etc/cron.d/deltagrid-market-sync}"
ENV_FILE="${ENV_FILE:-}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root to write ${CRON_FILE}" >&2
  exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
  echo "Project directory does not exist: ${PROJECT_DIR}" >&2
  exit 1
fi

touch "$LOG_FILE"
chmod 0644 "$LOG_FILE"

SYNC_ENV="COMPOSE_FILE=${COMPOSE_FILE}"
if [ -n "$ENV_FILE" ]; then
  SYNC_ENV="${SYNC_ENV} ENV_FILE=${ENV_FILE}"
fi
if [ -n "$COMPOSE_PROJECT_NAME" ]; then
  SYNC_ENV="${SYNC_ENV} COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}"
fi

cat > "$CRON_FILE" <<EOF
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

${SCHEDULE} root cd ${PROJECT_DIR} && ${SYNC_ENV} /bin/sh scripts/sync-market-data.sh --symbols ${SYMBOLS} --lookback-hours ${LOOKBACK_HOURS} --ohlcv-intervals ${OHLCV_INTERVALS} >> ${LOG_FILE} 2>&1
EOF

chmod 0644 "$CRON_FILE"

if command -v systemctl >/dev/null 2>&1; then
  systemctl reload cron >/dev/null 2>&1 || systemctl reload crond >/dev/null 2>&1 || true
fi

echo "Installed ${CRON_FILE}"
echo "Schedule: ${SCHEDULE}"
echo "Log: ${LOG_FILE}"
echo "Env file: ${ENV_FILE:-default from scripts/sync-market-data.sh}"
echo "Compose project: ${COMPOSE_PROJECT_NAME:-default}"
