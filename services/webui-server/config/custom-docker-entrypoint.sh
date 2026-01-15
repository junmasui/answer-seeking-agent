#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# NFS mounting logic (if requested)
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Running in NFS mode. Mounting file systems..."
    mount /mnt/frontend-nfs || echo "Warning: Failed to mount /mnt/frontend-nfs"
    mount /app/frontend || echo "Warning: Failed to mount /app/frontend"

    # Ensure directory exists before mounting
    mkdir -p /app/frontend/node_modules
    mount /app/frontend/node_modules || echo "Warning: Failed to mount /app/frontend/node_modules"

    # Wait for the NFS server/sync loop
    sleep 2
fi

# Volume initialization logic (must run as root)
echo "Initializing frontend volumes..."

# Identify potential volume mount points in the frontend container
FRONTEND_VOLS="/app/frontend/node_modules"

for VOL in $FRONTEND_VOLS
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
echo "Dropping privileges to node (UID 1000)..."
exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
