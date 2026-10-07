#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/oyra}"
cd "${PROJECT_DIR}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

COMPOSE_FILES=(-f docker-compose.yml)
if [ "${USE_HTTPS:-false}" = "true" ] && [ -d "/etc/letsencrypt/live/${DOMAIN:-oyra.com.ua}" ]; then
  COMPOSE_FILES+=(-f docker-compose.prod.yml)
fi

# nginx -s reload пише notice у stderr — certbot трактує це як помилку хука.
docker compose "${COMPOSE_FILES[@]}" exec -T nginx nginx -s reload 2>/dev/null
