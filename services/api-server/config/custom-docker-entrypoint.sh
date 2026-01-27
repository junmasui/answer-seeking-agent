#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from secrets
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
for FILE in "${SECRETS_MOUNT}"/*_secrets
do
    [ -f "$FILE" ] || continue
    while IFS='=' read -r KEY VALUE || [ -n "$KEY" ]; do
      case "$KEY" in
        \#* | '') continue ;;
        *) export "$KEY=$VALUE" ;;
      esac
    done < "$FILE"
done

# Volume initialization logic (must run as root)
echo "Initializing backend volumes..."

# Supervisor logic
# If USE_FUSE_SRC_DIR is true, or if we want to run supervisor generally.
# For now, let's switch to always running supervisor if this script is the entrypoint?
# Or only if FUSE is requested?
# To minimize disruption, let's use supervisor IF FUSE is requested, or maybe always?
# IF we run supervisor always, we need to make sure 'weed-mount' doesn't fail if not needed.
# But my supervisord.conf has 'weed-mount' as autostart=true.
# So we should only use supervisor if FUSE is enabled. 
# BUT, we want to unify?
# Let's stick to the plan: Robust FUSE mounting.
# So if USE_FUSE_SRC_DIR=true, use supervisor.
# If NOT, use the old flow? 
# Actually, 'weed-mount' failure might be bad if we force supervisor always.
# Let's make it conditional in the script.

if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
    echo "Running in FUSE mode with Supervisor..."
    
    # Ensure mount point exists
    mkdir -p /app/backend
    chown 1000:1000 /app/backend
    
    # Run supervisor
    # We rely on /etc/supervisord.conf
    # Pass the command arguments to supervisor via environment variable
    export APP_COMMAND="$*"
    export APP_AUTORESTART="${APP_AUTORESTART:-true}"
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    # Legacy/Standard flow (NFS or copy)
    echo "Running in Standard mode (No FUSE)..."
    
    # Identify potential volume mount points in the backend containers
    # API Server volumes
    API_VOLS="/staging"
    
    for VOL in $API_VOLS
    do
      if [ -d "$VOL" ]; then
        # Only initialize if it's a mount point (volume)
        # We check /proc/self/mounts as a robust way to identify mounts.
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
          echo "$VOL is part of the image, skipping initialization."
        fi
      fi
    done
    
    # Transition to the non-privileged entrypoint
    echo "Dropping privileges to python (UID 1000)..."
    exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
fi
