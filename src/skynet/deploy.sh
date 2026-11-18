#!/bin/bash
# Deployment script for skynet daemon service
# Run with: sudo ./deploy.sh

set -euo pipefail

SERVICE_NAME="skynet-daemon"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_SERVICE="${SCRIPT_DIR}/${SERVICE_NAME}.service"
TARGET_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

if [ ! -f "$SOURCE_SERVICE" ]; then
    echo "ERROR: Service definition not found at $SOURCE_SERVICE" >&2
    exit 1
fi

echo "Deploying ${SERVICE_NAME} from ${SOURCE_SERVICE}..."

# Install unit file
cp -f "$SOURCE_SERVICE" "$TARGET_SERVICE"
chmod 644 "$TARGET_SERVICE"

# Reload and restart
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo "✅ ${SERVICE_NAME} deployed and active."
