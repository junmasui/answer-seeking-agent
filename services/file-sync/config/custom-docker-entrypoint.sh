#!/bin/bash
set -euo pipefail

echo "Initializing file-sync service..."

# Load secrets (Common logic)
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
for FILE in "${SECRETS_MOUNT}"/*_secrets
do
    [ -f "$FILE" ] || continue
    while IFS='=' read -r KEY VALUE || [ -n "$KEY" ]; do
      case "$KEY" in
        \#* | '') continue ;;
        *) export "$KEY=$VALUE" ;;
      esac
    done < "$FILE"
done

# Ensure mount point exists
mkdir -p /mnt/fuse

# Run supervisor
echo "Starting Supervisord..."
exec /usr/bin/supervisord -c /etc/supervisord.conf
