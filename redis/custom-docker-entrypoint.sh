#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_env | xargs -n1 )
set -o history # turn it back on

cp ${SECRETS_MOUNT}/redis_conf redis.conf

cat redis.conf

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect redis:latest | jq '.[0].Config.Entrypoint'
exec docker-entrypoint.sh $@
