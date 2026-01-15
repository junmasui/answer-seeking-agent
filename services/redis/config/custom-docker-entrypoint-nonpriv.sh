#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

sed "s/\${REDIS_DEFAULT_PASSWORD}/${REDIS_DEFAULT_PASSWORD}/g" /redis.conf.template > redis.conf

cat redis.conf

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect redis:latest | jq '.[0].Config.Entrypoint'
exec docker-entrypoint.sh "$@"
