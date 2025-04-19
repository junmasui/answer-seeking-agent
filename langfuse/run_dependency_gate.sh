#!/usr/bin/env bash
set +e
set +x

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
set -o history # turn it back on

#
source /wait_for_gate.sh
source /wait_for_resource.sh

close_dependency_gate /init-signal/langfuse-gate

wait_for_resolv_conf


REDIS_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

wait_for_redis "${REDIS_URL}"

wait_for_minio "${MINIO_ENDPOINT_URL}"
wait_for_clickhouse "${CLICKHOUSE_URL}" "${CLICKHOUSE_USER}" "${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" "${CLICKHOUSE_DB}"

DATABASE_URL=postgres://langfuse:${LANGFUSE_POSTGRES_USER_PASSWORD}@pgvector:5432/langfuse

wait_for_pgvector "$DATABASE_URL"

open_dependency_gate /init-signal/langfuse-gate
