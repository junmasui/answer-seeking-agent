#!/usr/bin/env bash

set -e
set -u
set -o pipefail

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect opensearchproject/opensearch:2.9.0 | jq '.[0].Config.Entrypoint'
exec ./opensearch-docker-entrypoint.sh "$@"
