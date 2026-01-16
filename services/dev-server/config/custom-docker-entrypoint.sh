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

# Supervisor logic (if FUSE enabled)
if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
    echo "Running in FUSE mode with Supervisor..."
    
    mkdir -p /app
    
    # Run Supervisor with pre-baked config
    exec /usr/bin/supervisord -c /etc/supervisord.conf

else
    # Standard logic (No FUSE)
    
    # Transition to the non-privileged entrypoint
    echo "Dropping privileges to python (UID 1000)..."
    exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
fi
