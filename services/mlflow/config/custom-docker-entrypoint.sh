#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

# Build the backend store URI from individual postgres env vars
export MLFLOW_BACKEND_STORE_URI="postgresql://${MLFLOW_POSTGRES_USER_NAME:-mlflow}:${MLFLOW_POSTGRES_USER_PASSWORD}@${MLFLOW_POSTGRES_HOST}:${MLFLOW_POSTGRES_PORT}/${MLFLOW_POSTGRES_DATABASE}"

# Map S3 credentials to AWS env vars expected by MLflow
export AWS_ACCESS_KEY_ID="${MLFLOW_S3_ACCESS_KEY:-mlflow}"
export AWS_SECRET_ACCESS_KEY="${S3_SECRET_KEY}"

# Upgrade DB schema (required for 2.x → 3.x migration; no-op if already current)
mlflow db upgrade "${MLFLOW_BACKEND_STORE_URI}"

exec mlflow server \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri "${MLFLOW_BACKEND_STORE_URI}" \
    --default-artifact-root s3://mlflow \
    --serve-artifacts \
    --allowed-hosts "*"
