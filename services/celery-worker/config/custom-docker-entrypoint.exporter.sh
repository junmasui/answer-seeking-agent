#!/usr/bin/env bash

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )
export CE_BROKER_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker image inspect danihodovic/celery-exporter | jq '.[0].Config.Entrypoint'
exec python /app/cli.py "$@"
