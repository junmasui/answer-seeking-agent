#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

if [ "$USE_NFS_SRC_DIR" = "true" ]; then
    # The command must exactly match what is permitted in the /etc/sudoers file to avoid execution denial.
    sudo /usr/bin/mount /app/frontend
fi


exec "$@"
