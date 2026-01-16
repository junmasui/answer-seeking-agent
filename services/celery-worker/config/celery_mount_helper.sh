#!/usr/bin/env bash
set -euo pipefail

ECHO_PREFIX="[mount-helper]"
echo "$ECHO_PREFIX Waiting for mount at /app/backend..."

# Wait for mount
attempt=0
while ! mountpoint -q /app/backend; do
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 30 ]; then
        echo "$ECHO_PREFIX Error: Mount failed to appear after 30 seconds."
        exit 1
    fi
done

echo "$ECHO_PREFIX Mount active."

# Overlay .venv
# Celery worker specific logic: bind /app/.venv to /app/backend/.venv if /app/.venv exists
# Or fall back to /home/python/.venv-storage checks if needed (but celery compose maps volumes differently?)
# The previous script checked /app/.venv

if [ -d "/app/.venv" ] && ! mountpoint -q /app/backend/.venv; then
    echo "$ECHO_PREFIX Overlaying .venv from /app/.venv..."
    mkdir -p /app/backend/.venv
    mount --bind /app/.venv /app/backend/.venv || echo "$ECHO_PREFIX Warning: Failed to mount .venv"
elif [ -d "/home/python/.venv-storage" ] && ! mountpoint -q /app/backend/.venv; then
    echo "$ECHO_PREFIX Overlaying .venv from /home/python/.venv-storage..."
    mkdir -p /app/backend/.venv
    mount --bind /home/python/.venv-storage /app/backend/.venv || echo "$ECHO_PREFIX Warning: Failed to mount .venv"
fi

echo "$ECHO_PREFIX Done."
exit 0
