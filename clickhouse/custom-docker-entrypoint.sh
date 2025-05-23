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

# Copy files with sensitive data
[ -d /etc/clickhouse-server/users.d ] || mkdir -p /etc/clickhouse-server/users.d
cp "${SECRETS_MOUNT}/clickhouse_server_crt" /etc/clickhouse-server/server.crt
cp "${SECRETS_MOUNT}/clickhouse_server_key" /etc/clickhouse-server/server.key
cp "${SECRETS_MOUNT}/clickhouse_admin_user_xml" /etc/clickhouse-server/users.d/admin-user.xml


# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker image inspect clickhouse:24.12.3 | jq '.[0].Config.Entrypoint'
exec /entrypoint.sh "$@"
