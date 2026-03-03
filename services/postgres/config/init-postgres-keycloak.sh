#!/usr/bin/env bash

set -e  # Exit immediately on error.
#set -u  # Unbound variables are errors.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )


# Check for necessary environment variables
[ -z "${POSTGRES_HOST:-}" ] && echo "missing POSTGRES_HOST" && exit 1
[ -z "${POSTGRES_USER:-}" ] && echo "missing POSTGRES_USER" && exit 1
[ -z "${POSTGRES_PASSWORD:-}" ] && echo "missing POSTGRES_PASSWORD" && exit 1

[ -z "${KEYCLOAK_POSTGRES_USER_NAME:-}" ] && echo "missing KEYCLOAK_POSTGRES_USER_NAME" && exit 1
[ -z "${KEYCLOAK_POSTGRES_USER_PASSWORD:-}" ] && echo "missing KEYCLOAK_POSTGRES_USER_PASSWORD" && exit 1

export PGPASSWORD="$POSTGRES_PASSWORD"

envsubst < /init-keycloak-db.sql.template > /init-keycloak-db.sql
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -f /init-keycloak-db.sql
