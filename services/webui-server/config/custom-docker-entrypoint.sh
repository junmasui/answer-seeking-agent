#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    # If running with NFS, we need to mask node_modules with a tmpfs so it's container-local
    echo "Running in NFS mode. Mounting file systems..."
    # The command must exactly match what is permitted in the /etc/sudoers file to avoid execution denial.
    sudo /usr/bin/mount /mnt/frontend-nfs
    sudo /usr/bin/mount /app/frontend

    # Ensure directory exists before mounting
    mkdir -p /app/frontend/node_modules
    # Check if already mounted (to avoid double mounting if container restarts but didn't fully die?) 
    # Actually, simpler to just try mount.
    sudo /usr/bin/mount /app/frontend/node_modules
fi

cd /app/frontend


exec "$@"
