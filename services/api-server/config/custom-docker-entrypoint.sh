#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Volume initialization logic (must run as root)
echo "Initializing backend volumes..."

# NFS mounting logic (if requested)
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Running in NFS mode. Mounting file systems..."
    # These mounts require root privileges
    mount /mnt/backend-nfs || echo "Warning: Failed to mount /mnt/backend-nfs"
    mount /app/backend || echo "Warning: Failed to mount /app/backend"

    # Wait for the NFS server/sync loop
    sleep 2

    mkdir -p /app/backend/.venv
    mount /app/backend/.venv || echo "Warning: Failed to mount /app/backend/.venv"
fi

# Identify potential volume mount points in the backend containers
# API Server volumes
API_VOLS="/app/backend/.venv /staging"

for VOL in $API_VOLS
do
  if [ -d "$VOL" ]; then
    if [ ! -f "$VOL/.initialized" ]; then
      echo "Initializing $VOL..."
      touch "$VOL/.initialized"
      chown -R 1000:1000 "$VOL"
      chmod -R 755 "$VOL"
      ls -ld "$VOL"
    else
      echo "$VOL is already initialized."
    fi
  fi
done


# Transition to the non-privileged entrypoint
echo "Dropping privileges to python (UID 1000)..."
exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
