#!/usr/bin/env sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  printf 'Run as root or with sudo: sudo sh scripts/bootstrap-ubuntu.sh\n'
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

printf 'Updating apt indexes...\n'
apt-get update

printf 'Installing base packages...\n'
apt-get install -y \
  ca-certificates \
  certbot \
  curl \
  git \
  gnupg \
  nginx \
  openssl \
  python3 \
  python3-certbot-nginx \
  ufw

if ! command -v docker >/dev/null 2>&1; then
  printf 'Installing Docker from Ubuntu packages...\n'
  apt-get install -y docker.io docker-compose-plugin
else
  printf 'Docker already installed.\n'
fi

if ! docker compose version >/dev/null 2>&1; then
  printf 'Installing Docker Compose plugin...\n'
  apt-get install -y docker-compose-plugin
fi

systemctl enable --now docker
systemctl enable --now nginx

if command -v ufw >/dev/null 2>&1; then
  ufw allow OpenSSH || true
  ufw allow 'Nginx Full' || true
fi

printf 'Bootstrap complete. Docker, Compose, Nginx and Certbot are available.\n'
