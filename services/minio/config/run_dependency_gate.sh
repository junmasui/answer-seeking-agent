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

close_dependency_gate /init-signal/minio-gate

wait_for_resolv_conf

wait_for_nslookup "minio"

wait_for_minio "${MINIO_ENDPOINT_URL}"


open_dependency_gate /init-signal/minio-gate
