#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

echo "Initializing dev-server volumes..."

# Identify potential volume mount points
# The backend and frontend setup will happen in the non-priv script,
# but we need to ensure the shared volumes are owned by the python user.
DEV_VOLS="/home/python /home/python/.venv-storage /home/python/node_modules-storage"

for VOL in $DEV_VOLS
do
  if [ -d "$VOL" ]; then
    # Only initialize if it's a mount point (volume)
    if grep -q " $VOL " /proc/self/mounts; then
      echo "Initializing $VOL..."
      chown -R 1000:1000 "$VOL"
      chmod -R 755 "$VOL"
      ls -ld "$VOL"
    else
      echo "$VOL is part of the image, skipping initialization."
    fi
  fi
done

# NFS mounting logic (if requested)
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Mounting NFS directory..."
    if mountpoint -q /mnt/data; then
        echo "/mnt/data is already mounted."
    else
        mount /mnt/data || echo "Failed to mount /mnt/data"
    fi

    # Bind mount /mnt/data to /app
    echo "Bind mounting /mnt/data to /app..."
    mount /app || echo "Failed to mount /app"

    # Wait for the NFS server/sync loop
    sleep 2

    # Bind mount .venv from /home/python/.venv-storage
    echo "Bind mounting .venv..."
    mkdir -p /app/backend/.venv
    mount /app/backend/.venv || echo "Failed to mount /app/backend/.venv"

    # Bind mount node_modules
    echo "Bind mounting node_modules..."
    mkdir -p /app/frontend/node_modules
    mount /app/frontend/node_modules || echo "Failed to mount /app/frontend/node_modules"
fi

# Transition to the non-privileged entrypoint
echo "Dropping privileges to python (UID 1000)..."
exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
