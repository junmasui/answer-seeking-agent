#!/bin/bash
set -euo pipefail

echo "Starting file-sync service (Unison part)..."

# Environment variables
FILER_URL="${SEAWEEDFS_FILER:-seaweedfs:9002}"
MOUNT_DIR="/mnt/fuse"
SOURCE_DIR="/staging"

# Wait for SeaweedFS mount
echo "Waiting for mount at $MOUNT_DIR..."
attempt=0
while ! mountpoint -q "$MOUNT_DIR"; do
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 30 ]; then
        echo "Error: Mount failed to appear after 30 seconds."
        exit 1
    fi
done
echo "Mount active."

# Initial Sync (Host -> Fuse)
# We want to mirror the source (bind mount) to the fuse mount (S3).
echo "Starting initial Unison sync..."
unison "$SOURCE_DIR" "$MOUNT_DIR" \
    -auto -batch -terse -repeat 1 \
    -ignore "Name .venv" \
    -ignore "Name node_modules" \
    -ignore "Name __pycache__" \
    -ignore "Name .git"

# Watch mode (Continuous Sync)
echo "Starting continuous sync..."
unison "$SOURCE_DIR" "$MOUNT_DIR" \
    -auto -batch -terse -repeat watch \
    -ignore "Name .venv" \
    -ignore "Name node_modules" \
    -ignore "Name __pycache__" \
    -ignore "Name .git"
