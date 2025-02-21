#!/bin/bash

env | sort

[ -z "$CLICKHOUSE_DEFAULT_USER_PASSWORD" ] && echo "missing CLICKHOUSE_DEFAULT_USER_PASSWORD" && exit -1
[ -z "$CLICKHOUSE_ADMIN_USER" ] && echo "missing CLICKHOUSE_ADMIN_USER" && exit -1
[ -z "$LANGFUSE_CLICKHOUSE_USER_NAME" ] && echo "missing LANGFUSE_CLICKHOUSE_USER_NAME" && exit -1
[ -z "$LANGFUSE_CLICKHOUSE_USER_PASSWORD" ] && echo "missing LANGFUSE_CLICKHOUSE_USER_PASSWORD" && exit -1
[ -z "$LANGFUSE_CLICKHOUSE_DATABASE" ] && echo "missing LANGFUSE_CLICKHOUSE_DATABASE" && exit -1


call_clickhouse () {
    local command=$1
    local username=$2
    local password=$3
    local database=${4:-}

    declare -a headers=( \
        -H "X-ClickHouse-User: ${username}" \
        -H "X-ClickHouse-Key: ${password}" \
    )

    if [ -n "$database" ]; then
        headers+=( -H "X-ClickHouse-Database: ${database}" )
    fi

    (
        cat <<-EOS
        $command
EOS
    ) | curl -sS "${headers[@]}" 'http://localhost:8123/' --data-binary @-

}


call_clickhouse \
    "SELECT name, value FROM system.server_settings WHERE changed format Pretty" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"
call_clickhouse \
    "SELECT name, value FROM system.settings WHERE changed format Pretty" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

call_clickhouse \
    "show users format PrettyCompact" \
    "default" \
    "${CLICKHOUSE_DEFAULT_USER_PASSWORD}"

call_clickhouse \
    "CREATE DATABASE IF NOT EXISTS ${LANGFUSE_CLICKHOUSE_DATABASE}" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

call_clickhouse \
    "CREATE USER IF NOT EXISTS ${LANGFUSE_CLICKHOUSE_USER_NAME} IDENTIFIED BY '${LANGFUSE_CLICKHOUSE_USER_PASSWORD}'" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

# Assign default profile to the user
call_clickhouse \
    "ALTER USER ${LANGFUSE_CLICKHOUSE_USER_NAME} SETTINGS PROFILE 'default'" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

# Create a role
call_clickhouse \
    "CREATE ROLE IF NOT EXISTS langfuse_role" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

call_clickhouse \
    "GRANT langfuse_role TO langfuse" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

call_clickhouse \
    "GRANT ALL ON ${LANGFUSE_CLICKHOUSE_DATABASE}.* TO langfuse_role;" \
    admin \
    "${CLICKHOUSE_ADMIN_USER_PASSWORD}"

call_clickhouse \
    "SHOW TABLES format Pretty" \
    ${LANGFUSE_CLICKHOUSE_USER_NAME} \
    "${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" \
    ${LANGFUSE_CLICKHOUSE_DATABASE}

call_clickhouse \
    "SELECT name, value FROM system.settings WHERE changed format Pretty" \
    ${LANGFUSE_CLICKHOUSE_USER_NAME} \
    "${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" \
    ${LANGFUSE_CLICKHOUSE_DATABASE}
