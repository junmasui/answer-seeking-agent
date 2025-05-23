#!/usr/bin/env bash

## set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
## set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_env | xargs -n1 )
set -o history # turn it back on

# Wait for dependency-gate to open.
#
. /wait_for_gate.sh

wait_for_dependency_gate /init-signal/frontend-gate


# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect nginx:1.27.3-bookworm | jq '.[0].Config.Entrypoint'
exec /docker-entrypoint.sh "$@"
