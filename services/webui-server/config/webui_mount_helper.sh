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
# Logic from original entrypoint: checks /home/node/node_modules-storage or /home/node/node-modules-1
if [ -d "/home/node/node_modules-storage" ]; then
     echo "$ECHO_PREFIX Overlaying node_modules from /home/node/node_modules-storage..."
     mkdir -p /app/frontend/node_modules
     mount --bind /home/node/node_modules-storage /app/frontend/node_modules || echo "$ECHO_PREFIX Warn: Bind mount failed"
elif [ -d "/home/node/node-modules-1" ]; then
     echo "$ECHO_PREFIX Overlaying node_modules from /home/node/node-modules-1..."
     mkdir -p /app/frontend/node_modules
     mount --bind /home/node/node-modules-1 /app/frontend/node_modules || echo "$ECHO_PREFIX Warn: Bind mount failed"
fi

echo "$ECHO_PREFIX Done."
exit 0
