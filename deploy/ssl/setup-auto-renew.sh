#!/usr/bin/env bash
# Увімкнення автопродовження Let's Encrypt для Oyra (Docker nginx + certbot на хості).
#
# Критично: renew НЕ може бути standalone — порт 80 тримає nginx у Docker.
# Завжди webroot (/var/www/certbot) + deploy-hook reload nginx.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/oyra}"
DOMAIN="${DOMAIN:-oyra.com.ua}"
EMAIL="${EMAIL:-admin@${DOMAIN}}"
WEBROOT="/var/www/certbot"
HOOK_DIR="/etc/letsencrypt/renewal-hooks/deploy"
RENEWAL_CONF="/etc/letsencrypt/renewal/${DOMAIN}.conf"

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
RENEWAL_CONF="/etc/letsencrypt/renewal/${DOMAIN}.conf"

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

# Перевірка, що nginx віддає ACME з webroot (інакше renew знову впаде).
# Не використовуємо 127.0.0.1: Docker publish часто DNAT лише на зовнішній IP.
PROBE="oyra-acme-probe-$$"
PUB_IP="$(curl -fsS --max-time 5 https://ifconfig.me/ip 2>/dev/null || true)"
echo "ok" > "${WEBROOT}/.well-known/acme-challenge/${PROBE}"
ACME_OK=0
for target in \
  "http://${DOMAIN}/.well-known/acme-challenge/${PROBE}" \
  ${PUB_IP:+"http://${PUB_IP}/.well-known/acme-challenge/${PROBE}"}; do
  if curl -fsS --max-time 8 -H "Host: ${DOMAIN}" "${target}" | grep -qx 'ok'; then
    ACME_OK=1
    echo "==> ACME probe OK via ${target}"
    break
  fi
done
rm -f "${WEBROOT}/.well-known/acme-challenge/${PROBE}"
if [ "${ACME_OK}" -ne 1 ]; then
  echo "ERROR: nginx не віддає /.well-known/acme-challenge/ з ${WEBROOT}"
  echo "Переконайтесь, що docker.prod.conf змонтовано і контейнер nginx запущений."
  exit 1
fi

# Якщо в renewal ще standalone — force renew обов'язковий, щоб переписати authenticator.
FORCE_ARGS=()
if [ -f "${RENEWAL_CONF}" ] && grep -q 'authenticator = standalone' "${RENEWAL_CONF}"; then
  echo "==> renewal still standalone — forcing webroot reissue"
  FORCE_ARGS=(--force-renewal)
elif ! openssl x509 -checkend 2592000 -noout \
  -in "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" 2>/dev/null; then
  echo "==> cert expires within 30 days (or expired) — renewing now"
  FORCE_ARGS=(--force-renewal)
fi

certbot certonly --webroot \
  --webroot-path "${WEBROOT}" \
  -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --agree-tos -m "${EMAIL}" \
  --non-interactive \
  --preferred-challenges http \
  "${FORCE_ARGS[@]+"${FORCE_ARGS[@]}"}"

# Гарантуємо webroot у renewal.conf навіть якщо certbot лишив старі параметри.
if [ -f "${RENEWAL_CONF}" ]; then
  python3 - <<'PY' "${RENEWAL_CONF}" "${WEBROOT}"
import sys
from pathlib import Path

path = Path(sys.argv[1])
webroot = sys.argv[2]
text = path.read_text()
lines = []
in_renewal = False
seen_auth = False
seen_webroot = False
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith('[') and stripped.endswith(']'):
        in_renewal = stripped == '[renewalparams]'
    if in_renewal and stripped.startswith('authenticator'):
        lines.append('authenticator = webroot')
        seen_auth = True
        continue
    if in_renewal and stripped.startswith('webroot_path'):
        lines.append(f'webroot_path = {webroot},')
        seen_webroot = True
        continue
    lines.append(line)
if '[renewalparams]' in text:
    if not seen_auth:
        lines.append('authenticator = webroot')
    if not seen_webroot:
        lines.append(f'webroot_path = {webroot},')
path.write_text('\n'.join(lines) + '\n')
print(f'patched {path}')
PY
fi

# Deploy-hook після успішного renew
bash "${HOOK_DIR}/reload-oyra-nginx.sh" || true

systemctl enable --now certbot.timer
systemctl restart certbot.timer

echo "==> certbot.timer status"
systemctl is-active certbot.timer
systemctl list-timers certbot.timer --no-pager || true

echo "==> renewal authenticator"
grep -E '^(authenticator|webroot_path)' "${RENEWAL_CONF}" || true

echo "==> cert dates"
openssl x509 -in "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" -noout -dates

echo "==> dry-run renew (must succeed)"
certbot renew --dry-run --no-random-sleep-on-renew

echo "==> auto-renew OK (webroot + deploy hook reload nginx)"
