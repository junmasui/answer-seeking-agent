#!/usr/bin/env bash


# Error on unbound variables
set -u

#
# Wait for DNS /etc/resolv.conf to be correctly populated by Docker
#
function wait_for_resolv_conf {
    while true
    do
        grep -qE "nameserver[ \t]+(127\.0\.0\.11|172\.31\.1\.1)" /etc/resolv.conf
        if [ $? -eq 0 ]
        then
            echo "/etc/resolv.conf is populated"
            break
        fi
        sleep 2
    done
}

# Define multiple functions for waiting.
#

function wait_for_nslookup {
    declare LOOKUP_NAME="${1:-}"

    if [ -z "${LOOKUP_NAME:-}" ]
    then
        echo "LOOKUP_NAME is empty"
        exit 1
    fi

    while true
    do
        echo "waiting until DNS name ${LOOKUP_NAME} resolves"

        # Try with Docker's internal DNS
        nslookup "$LOOKUP_NAME" 127.0.0.11
        if [ $? -eq 0 ]
        then
            echo "DNS name ${LOOKUP_NAME} resolves"
            break
        fi

        # Try with Podman's DNS setup
        nslookup "$LOOKUP_NAME" 172.31.1.1
        if [ $? -eq 0 ]
        then
            echo "DNS name ${LOOKUP_NAME} resolves"
            break
        fi
        sleep 2
    done
}

function wait_for_minio {
    declare MINIO_ENDPOINT_URL=${1:-}

    if [ -z "${MINIO_ENDPOINT_URL:-}" ]
    then
        echo "MINIO_ENDPOINT_URL is empty"
        exit 1
    fi

    #
    # Wait for DNS resolution of minio
    #
    wait_for_nslookup minio

    #
    # Wait for minio to be ready
    #
    echo "waiting for minio to be ready"
    while true
    do
        curl -f "${MINIO_ENDPOINT_URL}/minio/health/live"
        if [ $? -eq 0 ]
        then
            echo "minio is live"
            break
        fi
        sleep 2
    done

    ### TODO - Wait for user and bucket

}

function wait_for_pgvector {
    declare DATABASE_URL=${1:-}

    if [ -z "${DATABASE_URL:-}" ]
    then
        echo "DATABASE_URL is empty"
        exit 1
    fi

    #
    # Wait for DNS resolution of postgres
    #
    wait_for_nslookup pgvector

    #
    # Wait for postgres to be ready
    #
    echo "waiting for postgres to be ready"
    while true
    do
        pg_isready -d "${DATABASE_URL}"
        if [ $? -eq 0 ]
        then
            echo "postgres is ready"
            break
        fi
        sleep 2
    done

    ### TODO - Wait for user and schema
}

function wait_for_clickhouse {
    declare CLICKHOUSE_URL=${1:-}
    declare CLICKHOUSE_USER=${2:-}
    declare CLICKHOUSE_PASSWORD=${3:-}
    declare CLICKHOUSE_DB=${4:-}

    if [ -z "${CLICKHOUSE_URL:-}" ]
    then
        echo "CLICKHOUSE_URL is empty"
        exit 1
    fi

    #
    # Wait for DNS resolution of clickhouse
    #
    wait_for_nslookup clickhouse

    #
    # Wait for clickhouse to be ready
    #
    echo "waiting for clickhouse to be ready"
    while true
    do
        curl -u "${CLICKHOUSE_USER}:${CLICKHOUSE_PASSWORD}" -f "${CLICKHOUSE_URL}/?database=${CLICKHOUSE_DB}&query=SHOW%20TABLES"
        if [ $? -eq 0 ]
        then
            echo "clickhouse is live"
            break
        fi
        sleep 2
    done
}


function wait_for_redis {
    declare REDIS_URL=${1:-}

    echo redis
    echo "$@"
    echo redis

    if [ -z "${REDIS_URL:-}" ]
    then
        echo "REDIS_URL is empty"
        exit 1
    fi

    #
    # Wait for DNS resolution of redis
    #
    wait_for_nslookup redis

    #
    # Wait for redis to be ready
    #
    echo "Waiting for redis to be ready"
    while true
    do
        redis-cli -u "${REDIS_URL}" ping
        if [ $? -eq 0 ]
        then
            echo "redis is live"
            break
        fi
        sleep 2
    done
}
