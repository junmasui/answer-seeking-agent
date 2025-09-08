#!/usr/bin/env bash
set +e
set +x

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

#
source /wait_for_gate.sh
source /wait_for_resource.sh

close_dependency_gate /init-signal/frontend-gate

wait_for_resolv_conf


wait_for_nslookup "$VITE_SERVER_HOST"
wait_for_nslookup "$FASTAPI_HOST"


open_dependency_gate /init-signal/frontend-gate
