#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

echo "Initializing dev-server volumes..."

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
