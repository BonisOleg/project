#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/oyra}"
DOMAIN="${DOMAIN:-oyra.com.ua}"
EMAIL="${EMAIL:-admin@${DOMAIN}}"
WEBROOT="/var/www/certbot"
HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: run as root"
  exit 1
fi

cd "${PROJECT_DIR}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

DOMAIN="${DOMAIN:-oyra.com.ua}"
EMAIL="${EMAIL:-admin@${DOMAIN}}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq certbot

mkdir -p "${WEBROOT}/.well-known/acme-challenge"
mkdir -p "${HOOK_DIR}"

install -m 755 "${PROJECT_DIR}/deploy/ssl/reload-nginx.sh" "${HOOK_DIR}/reload-oyra-nginx.sh"

if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  echo "ERROR: no existing cert at /etc/letsencrypt/live/${DOMAIN}"
  echo "Issue first with DEPLOY.md §3.3, then re-run this script."
  exit 1
fi

certbot certonly --webroot \
  --webroot-path "${WEBROOT}" \
  -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --agree-tos -m "${EMAIL}" \
  --keep-until-expiry \
  --non-interactive \
  --preferred-challenges http

systemctl enable --now certbot.timer
systemctl restart certbot.timer

echo "==> certbot.timer status"
systemctl is-active certbot.timer
systemctl list-timers certbot.timer --no-pager || true

echo "==> dry-run renew"
certbot renew --dry-run

echo "==> auto-renew OK (webroot + deploy hook reload nginx)"
