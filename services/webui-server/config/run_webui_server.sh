#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )


# If running with NFS, we need to mask node_modules with a tmpfs so it's container-local
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Running in NFS mode. Mounting tmpfs on node_modules..."
    # Ensure directory exists before mounting
    mkdir -p node_modules
    # Check if already mounted (to avoid double mounting if container restarts but didn't fully die?) 
    # Actually, simpler to just try mount.
    sudo mount -t tmpfs tmpfs /app/frontend/node_modules
fi

# Install dependencies
npm install

# Start the Vite (Vue.js) development server
npm run dev -- --host 0.0.0.0 --logLevel info
