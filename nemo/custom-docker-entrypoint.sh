#!/usr/bin/env bash

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_env | xargs -n1 )
set -o history # turn it back on

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect nemoguardrails:latest | jq '.[0].Config.Entrypoint'
exec uv run nemoguardrails "$@"
