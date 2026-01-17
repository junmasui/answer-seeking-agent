#!/usr/bin/env bash
set -euo pipefail

# Only run if FUSE is enabled
if [ "${USE_FUSE_SRC_DIR:-false}" != "true" ]; then
    exit 0
fi

ECHO_PREFIX="[mount-helper]"
echo "$ECHO_PREFIX Waiting for mount at /app/frontend..."

# Wait for mount
attempt=0
while ! mountpoint -q /app/frontend; do
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 30 ]; then
        echo "$ECHO_PREFIX Error: Mount failed to appear after 30 seconds."
        exit 1
    fi
done

echo "$ECHO_PREFIX Mount active."

# Overlay node_modules
# Create and mount local node_modules to avoid sharing the ephemral node_modules
# directory across multiple containers.
LOCAL_MODULES="/home/node/node_modules-storage"
if [ ! -d "$LOCAL_MODULES" ]; then
    echo "$ECHO_PREFIX Creating local storage at $LOCAL_MODULES..."
    mkdir -p "$LOCAL_MODULES"
    chown 1000:1000 "$LOCAL_MODULES"
fi

echo "$ECHO_PREFIX Overlaying node_modules from $LOCAL_MODULES..."
mkdir -p /app/frontend/node_modules
mount --bind "$LOCAL_MODULES" /app/frontend/node_modules || echo "$ECHO_PREFIX Warn: Bind mount failed"

echo "$ECHO_PREFIX Done."
exit 0
