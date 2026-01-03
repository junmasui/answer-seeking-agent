#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )


# Install dependencies
# Use npm ci to ensure we strictly follow package-lock.json and do not attempt to write to it.
# This prevents permission errors if package-lock.json is read-only or owned by another user.
set +e
npm ci
EXIT_CODE=$?
set -e

if [ $EXIT_CODE -ne 0 ]; then
    echo "Error: npm ci failed."
    echo "This is likely because package-lock.json is not up-to-date with package.json."
    echo "Please run 'npm install' on your host machine to update package-lock.json."
    exit $EXIT_CODE
fi

# Start the Vite (Vue.js) development server
npm run dev -- --host 0.0.0.0 --logLevel info
