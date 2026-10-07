#!/usr/bin/env bash
# Термінове оновлення сертифіката (webroot) + reload nginx.
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/var/www/oyra}"
cd "${PROJECT_DIR}"
exec bash "${PROJECT_DIR}/deploy/ssl/setup-auto-renew.sh"
