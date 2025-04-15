#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )

export GF_SECURITY_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD
set -o history # turn it back on

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect grafana/grafana:RELEASE.2024-12-13T22-19-12Z | jq '.[0].Config.Entrypoint'
exec /run.sh $@
