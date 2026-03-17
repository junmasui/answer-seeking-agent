#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

# Prevent Playwright from downloading browser binaries at npm install time.
# The Docker image already has system Chromium at /usr/bin/chromium.
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

if [ "${ENABLE_MUTAGEN_SYNC:-false}" = "true" ]; then
    echo "Waiting for e2e/ directory..."
    attempt=0
    while [ ! -f /app/e2e/package.json ]; do
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 60 ]; then
            echo "Error: /app/e2e/package.json did not appear after 60 seconds."
            exit 1
        fi
    done
    echo "/app/e2e detected."
fi

cd /app/e2e
npm install

echo "Starting Xvfb on :99..."
Xvfb :99 -screen 0 1280x720x24 -ac &
XVFB_PID=$!
export DISPLAY=:99
sleep 1

export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium
npm test
TEST_EXIT_CODE=$?

kill $XVFB_PID 2>/dev/null || true
exit $TEST_EXIT_CODE
