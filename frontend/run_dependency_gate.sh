#!/usr/bin/env bash
set +e
set +x

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_env | xargs -n1 )
set -o history # turn it back on

#
source /wait_for_gate.sh
source /wait_for_resource.sh

close_dependency_gate /init-signal/frontend-gate

wait_for_resolv_conf


wait_for_nslookup $VITE_SERVER_HOST
wait_for_nslookup $FASTAPI_HOST


open_dependency_gate /init-signal/frontend-gate
