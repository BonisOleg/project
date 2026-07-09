#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${PROJECT_DIR}"

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Copy .env.example to .env and configure it."
  exit 1
fi

# shellcheck disable=SC1091
set -a
source .env
set +a

echo "==> Freeing ports 80 and 443 on host..."
for port in 80 443; do
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" 2>/dev/null || true
  fi
done

echo "==> Stopping host nginx/gunicorn if running..."
systemctl stop nginx 2>/dev/null || true
systemctl stop 'gunicorn-*' 2>/dev/null || true

COMPOSE_FILES=(-f docker-compose.yml)
DOMAIN="${DOMAIN:-your-domain.com}"

if [ "${USE_HTTPS:-false}" = "true" ] && [ -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  echo "==> HTTPS mode: using docker-compose.prod.yml"
  COMPOSE_FILES+=(-f docker-compose.prod.yml)
else
  echo "==> HTTP mode: docker.conf only (set USE_HTTPS=true after certbot)"
fi

echo "==> Building and starting containers..."
docker compose "${COMPOSE_FILES[@]}" up -d --build

echo "==> Waiting for healthcheck..."
sleep 5

if curl -sf "http://127.0.0.1/healthz/" >/dev/null; then
  echo "==> HTTP healthcheck OK"
else
  echo "WARN: HTTP healthcheck failed — check logs: docker compose logs web nginx"
  exit 1
fi

if [ "${USE_HTTPS:-false}" = "true" ] && [ -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  if curl -sfk "https://127.0.0.1/healthz/" >/dev/null; then
    echo "==> HTTPS healthcheck OK"
  else
    echo "WARN: HTTPS healthcheck failed — check nginx SSL paths for DOMAIN=${DOMAIN}"
  fi
fi

docker compose "${COMPOSE_FILES[@]}" ps
echo "==> Deploy complete"
