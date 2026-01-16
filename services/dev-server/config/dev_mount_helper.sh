#!/usr/bin/env bash
set -euo pipefail

ECHO_PREFIX="[mount-helper]"
echo "$ECHO_PREFIX Waiting for mount at /app..."

# Wait for mount
attempt=0
while ! mountpoint -q /app; do
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 30 ]; then
        echo "$ECHO_PREFIX Error: Mount failed to appear after 30 seconds."
        exit 1
    fi
done

echo "$ECHO_PREFIX Mount active."

# Overlay persistence volumes
# .venv
if [ -d "/home/python/.venv-storage" ]; then
    echo "$ECHO_PREFIX Overlaying .venv..."
    mkdir -p /app/backend/.venv
    mount --bind /home/python/.venv-storage /app/backend/.venv || echo "$ECHO_PREFIX Warn: Failed .venv bind"
fi

# node_modules
if [ -d "/home/python/node_modules-storage" ]; then
    echo "$ECHO_PREFIX Overlaying node_modules..."
    mkdir -p /app/frontend/node_modules
    mount --bind /home/python/node_modules-storage /app/frontend/node_modules || echo "$ECHO_PREFIX Warn: Failed node_modules bind"
fi

echo "$ECHO_PREFIX Done."
exit 0
