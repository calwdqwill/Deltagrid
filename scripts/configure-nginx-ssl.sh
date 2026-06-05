#!/usr/bin/env sh
set -eu

DOMAIN="${DOMAIN:-deltagrid.pro}"
EMAIL="${LETSENCRYPT_EMAIL:-}"
APP_DIR="${APP_DIR:-$(pwd)}"
SITE_NAME="${SITE_NAME:-deltagrid}"
NGINX_AVAILABLE="/etc/nginx/sites-available/$SITE_NAME"
NGINX_ENABLED="/etc/nginx/sites-enabled/$SITE_NAME"

if [ "$(id -u)" -ne 0 ]; then
  printf 'Run as root or with sudo: sudo DOMAIN=%s sh scripts/configure-nginx-ssl.sh\n' "$DOMAIN"
  exit 1
fi

if [ ! -f "$APP_DIR/deploy/nginx/deltagrid.conf.example" ]; then
  printf 'Nginx template not found at %s/deploy/nginx/deltagrid.conf.example\n' "$APP_DIR"
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

cp "$APP_DIR/deploy/nginx/deltagrid.conf.example" "$NGINX_AVAILABLE"

if [ ! -e "$NGINX_ENABLED" ]; then
  ln -s "$NGINX_AVAILABLE" "$NGINX_ENABLED"
fi

nginx -t
systemctl reload nginx

printf 'Requesting SSL certificate for %s and www.%s...\n' "$DOMAIN" "$DOMAIN"
if [ -n "$EMAIL" ]; then
  certbot --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect
else
  printf 'LETSENCRYPT_EMAIL is empty; issuing without expiry email notifications.\n'
  certbot --nginx \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --register-unsafely-without-email \
    --redirect
fi

nginx -t
systemctl reload nginx

printf 'Nginx and SSL are configured for %s.\n' "$DOMAIN"
