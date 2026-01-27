#!/usr/bin/env bash
set -euo pipefail

# Only run if FUSE is enabled
if [ "${USE_FUSE_SRC_DIR:-false}" != "true" ]; then
    echo "FUSE not enabled. Helper exiting."
    exit 0
fi

ECHO_PREFIX="[mount-helper]"
echo "$ECHO_PREFIX Waiting for mount at /app/backend..."

# Wait for mount
attempt=0
while ! mountpoint -q /app/backend; do
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 30 ]; then
        echo "$ECHO_PREFIX Error: Mount failed to appear after 30 seconds."
        # We exit 1, which puts this service in FAILED state.
        # This doesn't stop other services in supervisor unless we use an event listener, 
        # but it alerts the user via logs.
        exit 1
    fi
done

echo "$ECHO_PREFIX Mount active."

# Bind Mounts
if [ -d "/home/python/.venv-storage" ]; then
     echo "$ECHO_PREFIX Overlaying .venv from /home/python/.venv-storage..."
     mkdir -p /app/backend/.venv
     
     # Check if already mounted (in case of restart)
     if ! mountpoint -q /app/backend/.venv; then
        mount --bind /home/python/.venv-storage /app/backend/.venv || echo "$ECHO_PREFIX Warning: Failed to mount .venv"
        echo "$ECHO_PREFIX .venv mounted."
     else
        echo "$ECHO_PREFIX .venv already mounted."
     fi
else
     echo "$ECHO_PREFIX Warning: /home/python/.venv-storage not found."
fi

echo "$ECHO_PREFIX Done."
exit 0
