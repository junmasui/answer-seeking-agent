#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# FUSE mounting logic (if requested)
# Supervisor logic
if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
    echo "Running in FUSE mode with Supervisor..."
    
    mkdir -p /app/frontend
    
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    # Standard Mode
    
    # Volume initialization logic (must run as root)
    echo "Initializing frontend volumes..."
    
    # Identify potential volume mount points in the frontend container
    FRONTEND_VOLS="/app/frontend/node_modules"
    
    for VOL in $FRONTEND_VOLS
    do
      if [ -d "$VOL" ]; then
        # Only initialize if it's a mount point (volume)
        if grep -q " $VOL " /proc/self/mounts; then
          if [ ! -f "$VOL/.initialized" ]; then
            echo "Initializing $VOL..."
            touch "$VOL/.initialized"
            chown -R 1000:1000 "$VOL"
            chmod -R 755 "$VOL"
            ls -ld "$VOL"
          else
            echo "$VOL is already initialized."
          fi
        else
          # echo "$VOL is part of the image, skipping initialization."
          :
        fi
      fi
    done
    
    # Transition to the non-privileged entrypoint
    echo "Dropping privileges to node (UID 1000)..."
    exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
fi

