#!/usr/bin/env sh
set -eu

DOMAIN="${DOMAIN:-preview.deltagrid.pro}"
EMAIL="${LETSENCRYPT_EMAIL:-}"
APP_DIR="${APP_DIR:-$(pwd)}"
SITE_NAME="${SITE_NAME:-deltagrid-preview}"
TEMPLATE="${TEMPLATE:-$APP_DIR/deploy/nginx/deltagrid-preview.conf.example}"
SKIP_DNS_CHECK="${SKIP_DNS_CHECK:-false}"
NGINX_AVAILABLE="/etc/nginx/sites-available/$SITE_NAME"
NGINX_ENABLED="/etc/nginx/sites-enabled/$SITE_NAME"

if [ "$(id -u)" -ne 0 ]; then
  printf 'Run as root or with sudo: sudo DOMAIN=%s sh scripts/configure-preview-nginx-ssl.sh\n' "$DOMAIN"
  exit 1
fi

if [ ! -f "$TEMPLATE" ]; then
  printf 'Nginx template not found: %s\n' "$TEMPLATE"
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
  printf 'nginx is not installed. Run sudo sh scripts/bootstrap-ubuntu.sh first.\n'
  exit 1
fi

if ! command -v certbot >/dev/null 2>&1; then
  printf 'certbot is not installed. Run sudo sh scripts/bootstrap-ubuntu.sh first.\n'
  exit 1
fi

if [ "$SKIP_DNS_CHECK" != "true" ] && ! getent hosts "$DOMAIN" >/dev/null 2>&1; then
  printf 'DNS for %s does not resolve yet. Add the DNS record first or rerun with SKIP_DNS_CHECK=true.\n' "$DOMAIN"
  exit 2
fi

cp "$TEMPLATE" "$NGINX_AVAILABLE"

if [ ! -e "$NGINX_ENABLED" ]; then
  ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
fi

nginx -t
systemctl reload nginx

printf 'Requesting SSL certificate for %s...\n' "$DOMAIN"
if [ -n "$EMAIL" ]; then
  certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect
else
  printf 'LETSENCRYPT_EMAIL is empty; issuing without expiry email notifications.\n'
  certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --redirect
fi

nginx -t
systemctl reload nginx

printf 'Nginx and SSL are configured for %s.\n' "$DOMAIN"
