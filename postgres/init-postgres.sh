#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
## set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

## set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
## set -o history # turn it back on

# Check for necessary environment variables
[ -z "${POSTGRES_HOST:-}" ] && echo "missing POSTGRES_HOST" && exit 1
[ -z "${POSTGRES_USER:-}" ] && echo "missing POSTGRES_USER" && exit 1
[ -z "${POSTGRES_PASSWORD:-}" ] && echo "missing POSTGRES_PASSWORD" && exit 1

[ -z "${BACKEND_POSTGRES_DATABASE:-}" ] && echo "missing BACKEND_POSTGRES_DATABASE" && exit 1
[ -z "${BACKEND_POSTGRES_USER_NAME:-}" ] && echo "missing BACKEND_POSTGRES_USER_NAME" && exit 1
[ -z "${BACKEND_POSTGRES_USER_PASSWORD:-}" ] && echo "missing BACKEND_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${BACKEND_VECTORS_POSTGRES_USER_NAME:-}" ] && echo "missing BACKEND_VECTORS_POSTGRES_USER_NAME" && exit 1
[ -z "${BACKEND_VECTORS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing BACKEND_VECTORS_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${BACKEND_CHECKPOINTS_POSTGRES_USER_NAME:-}" ] && echo "missing BACKEND_CHECKPOINTS_POSTGRES_USER_NAME" && exit 1
[ -z "${BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD" && exit 1

[ -z "${ANSWERS_TEST_POSTGRES_DATABASE:-}" ] && echo "missing ANSWERS_TEST_POSTGRES_DATABASE" && exit 1
[ -z "${ANSWERS_TEST_POSTGRES_USER_NAME:-}" ] && echo "missing ANSWERS_TEST_POSTGRES_USER_NAME" && exit 1
[ -z "${ANSWERS_TEST_POSTGRES_USER_PASSWORD:-}" ] && echo "missing ANSWERS_TEST_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${ANSWERS_TEST_VECTORS_POSTGRES_USER_NAME:-}" ] && echo "missing ANSWERS_TEST_VECTORS_POSTGRES_USER_NAME" && exit 1
[ -z "${ANSWERS_TEST_VECTORS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing ANSWERS_TEST_VECTORS_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_NAME:-}" ] && echo "missing ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_NAME" && exit 1
[ -z "${ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_PASSWORD:-}" ] && echo "missing ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_PASSWORD" && exit 1

[ -z "${LANGFUSE_POSTGRES_USER_NAME:-}" ] && echo "missing LANGFUSE_POSTGRES_USER_NAME" && exit 1
[ -z "${LANGFUSE_POSTGRES_USER_PASSWORD:-}" ] && echo "missing LANGFUSE_POSTGRES_USER_PASSWORD" && exit 1
[ -z "${LANGFUSE_POSTGRES_DATABASE:-}" ] && echo "missing LANGFUSE_POSTGRES_DATABASE" && exit 1


export PGPASSWORD=$POSTGRES_PASSWORD

envsubst < /init-db.sql.template > /init-db.sql
sleep 10
psql -h pgvector -U $POSTGRES_USER -f /init-db.sql

envsubst < /init-langfuse-db.sql.template > /init-langfuse-db.sql
sleep 10
psql -h pgvector -U $POSTGRES_USER -f /init-langfuse-db.sql


export BACKEND_POSTGRES_DATABASE=$ANSWERS_TEST_POSTGRES_DATABASE

export BACKEND_POSTGRES_USER_NAME=$ANSWERS_TEST_POSTGRES_USER_NAME
export BACKEND_POSTGRES_USER_PASSWORD=$ANSWERS_TEST_POSTGRES_USER_PASSWORD
export BACKEND_VECTORS_POSTGRES_USER_NAME=$ANSWERS_TEST_VECTORS_POSTGRES_USER_NAME
export BACKEND_VECTORS_POSTGRES_USER_PASSWORD=$ANSWERS_TEST_VECTORS_POSTGRES_USER_PASSWORD
export BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD=$ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_NAME
export BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD=$ANSWERS_TEST_CHECKPOINTS_POSTGRES_USER_PASSWORD

envsubst < /init-db.sql.template > /init-db.sql
sleep 10
psql -h pgvector -U $POSTGRES_USER -f /init-db.sql
