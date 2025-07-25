#!/usr/bin/env bash

set -e  # Exit immediately on error.
#set -u  # Unbound variables are errors.
## set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

## TODO FIXME set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )
## TODO FIXME set -o history # turn it back on

# Wait for dependency-gate to open.
#

. /wait_for_gate.sh


# Check for necessary environment variables
[ -z "${POSTGRES_HOST:-}" ] && echo "missing POSTGRES_HOST" && exit 1
[ -z "${POSTGRES_USER:-}" ] && echo "missing POSTGRES_USER" && exit 1
[ -z "${POSTGRES_PASSWORD:-}" ] && echo "missing POSTGRES_PASSWORD" && exit 1

[ -z "${ANSWERS_POSTGRES_DATABASE:-}" ] && echo "missing ANSWERS_POSTGRES_DATABASE" && exit 1
[ -z "${ANSWERS_POSTGRES_USER_NAME:-}" ] && echo "missing ANSWERS_POSTGRES_USER_NAME" && exit 1
[ -z "${ANSWERS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing ANSWERS_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${CHECKPOINTS_POSTGRES_USER_NAME:-}" ] && echo "missing CHECKPOINTS_POSTGRES_USER_NAME" && exit 1
[ -z "${CHECKPOINTS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing CHECKPOINTS_POSTGRES_USER_PASSWORD" && exit 1

wait_for_dependency_gate /init-signal/postgres-gate

export PGPASSWORD="$POSTGRES_PASSWORD"

envsubst < /init-db.sql.template > /init-db.sql
sleep 10
psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -f /init-db.sql

