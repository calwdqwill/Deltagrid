#!/usr/bin/env sh
set -eu

DOMAIN="${1:-${DOMAIN:-deltagrid.pro}}"
OUT_FILE="${ENV_FILE:-.env.production}"

if [ -f "$OUT_FILE" ]; then
  printf '%s already exists. Remove it or set ENV_FILE to another path.\n' "$OUT_FILE"
  exit 1
fi

if command -v openssl >/dev/null 2>&1; then
  SECRET_KEY="$(openssl rand -hex 32)"
  POSTGRES_PASSWORD="$(openssl rand -hex 24)"
else
  printf 'openssl is required to generate secrets.\n'
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  VAULT_MASTER_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' 2>/dev/null || true)"
  if [ -z "$VAULT_MASTER_KEY" ]; then
    VAULT_MASTER_KEY="$(python3 -c 'import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())')"
  fi
else
  printf 'python3 is required to generate VAULT_MASTER_KEY.\n'
  exit 1
fi

cat > "$OUT_FILE" <<EOF
APP_NAME=DeltaGrid
DEBUG=false

PUBLIC_APP_URL=https://$DOMAIN
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization,X-Request-ID,X-API-Version
NEXT_PUBLIC_WS_URL=

SECRET_KEY=$SECRET_KEY
VAULT_MASTER_KEY=$VAULT_MASTER_KEY

POSTGRES_DB=deltagrid
POSTGRES_USER=deltagrid
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
DATABASE_URL=postgresql://deltagrid:$POSTGRES_PASSWORD@postgres:5432/deltagrid

COINGECKO_API_KEY=
COINGLASS_API_KEY=
COINGLASS_STANDARD_API_KEY=

CACHE_TTL_SECONDS=60
CACHE_MAX_SIZE=1000
EOF

chmod 600 "$OUT_FILE"
printf 'Created %s for %s. Fill provider API keys if needed before deploy.\n' "$OUT_FILE" "$DOMAIN"
