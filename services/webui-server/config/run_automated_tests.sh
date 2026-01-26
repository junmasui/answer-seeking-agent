#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )


if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
    # Install dependencies
    # Determine install command based on whether node_modules is a mount point
    # npm ci tries to remove the node_modules directory which fails on mount points.
    NPM_CMD="npm install"
    if grep -q " /app/frontend/node_modules " /proc/mounts; then
        echo "node_modules is a bind mount. Using npm install."
        NPM_CMD="npm install"
    fi

    set +e
    $NPM_CMD
    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -ne 0 ]; then
        echo "Error: $NPM_CMD failed. Attempting to recover by cleaning cache..."
        npm cache clean --force
        $NPM_CMD
        EXIT_CODE=$?
    fi

    if [ $EXIT_CODE -ne 0 ]; then
        echo "Error: npm ci failed again after cache clean."
        echo "This is likely because package-lock.json is not up-to-date with package.json."
        echo "Please run 'npm install' on your host machine to update package-lock.json."
        exit $EXIT_CODE
    fi
fi

npm run test:unit
