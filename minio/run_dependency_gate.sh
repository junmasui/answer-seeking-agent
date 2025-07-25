#!/usr/bin/env bash
set +e
set +x

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )
set -o history # turn it back on

#
source /wait_for_gate.sh
source /wait_for_resource.sh

close_dependency_gate /init-signal/minio-gate

wait_for_resolv_conf

wait_for_nslookup "minio"

wait_for_minio "${MINIO_ENDPOINT_URL}"


open_dependency_gate /init-signal/minio-gate
