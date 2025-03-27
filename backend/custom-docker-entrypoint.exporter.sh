#!/usr/bin/env bash

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
set -o history # turn it back on

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker image inspect danihodovic/celery-exporter | jq '.[0].Config.Entrypoint'
exec python /app/cli.py $@
