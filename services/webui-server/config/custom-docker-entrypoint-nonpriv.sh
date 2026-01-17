#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )


# Only run if FUSE is enabled
if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then

    echo "Waiting for mount at /app/frontend..."

    # Wait for mount
    attempt=0
    while ! mountpoint -q /app/frontend; do
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 30 ]; then
            echo "Error: Mount failed to appear after 30 seconds."
            exit 1
        fi
    done

    echo "Mount active."
fi

# Transition to the non-privileged entrypoint

cd /app/frontend


exec "$@"
