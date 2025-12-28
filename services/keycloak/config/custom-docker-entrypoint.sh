#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

# Map generated secrets to Keycloak expected variables
export KC_BOOTSTRAP_ADMIN_USERNAME="${KEYCLOAK_ADMIN}"
export KC_BOOTSTRAP_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}"

export KC_DB_PASSWORD="${KEYCLOAK_POSTGRES_USER_PASSWORD}"

env | sort

# Process with original command
exec /opt/keycloak/bin/kc.sh "$@"
