#!/bin/sh


# See the original entrypoint that we are replacing:
# https://github.com/langfuse/langfuse/blob/main/web/Dockerfile#L142

# Error on unbound variables
set -u

#
# Wait for DNS /etc/resolv.conf to be correctly populated by Docker
#
while true
do
    grep -qE "nameserver[ \t]+127\.0\.0\.11" /etc/resolv.conf
    if [ $? -eq 0 ]
    then
        echo "/etc/resolv.conf is populated"
        break
    fi
    sleep 2
done


function wait_for_nslookup {
    TARGET_NAME=$1
    while true
    do
        nslookup $TARGET_NAME 127.0.0.11
        if [ $? -eq 0 ]
        then
            echo "DNS name ${TARGET_NAME} resolves"
            break
        fi
        sleep 2
    done
}


# Ensure that the case of unset MINIO_ENDPOINT_URL is handled.
if [ ! -z "${MINIO_ENDPOINT_URL:-}" ]
then
    #
    # Wait for DNS resolution of minio
    #
    wait_for_nslookup minio

    #
    # Wait for minio to be ready
    #
    echo "Waiting for minio to be ready"
    while true
    do
        curl -f ${MINIO_ENDPOINT_URL}/minio/health/live
        if [ $? -eq 0 ]
        then
            echo "minio is live"
            break
        fi
        sleep 2
    done
fi

# Ensure that the case of unset DATABASE_URL is handled.
if [ ! -z "${DATABASE_URL:-}" ]
then
    #
    # Wait for DNS resolution of postgres
    #
    wait_for_nslookup pgvector

    #
    # Wait for postgres to be ready
    #
    echo "Waiting for postgres to be ready"
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
fi

# Ensure that the case of unset CLICKHOUSE_URL is handled.
if [ ! -z "${CLICKHOUSE_URL:-}" ]
then
    #
    # Wait for DNS resolution of clickhouse
    #
    wait_for_nslookup clickhouse

    #
    # Wait for clickhouse to be ready
    #
    echo "Waiting for clickhouse to be ready"
    while true
    do
        curl -f -H "X-Clickhouse-Database: ${CLICKHOUSE_DB}" -H "X-Clickhouse-User: ${CLICKHOUSE_USER}"  -H "X-Clickhouse-Key: ${CLICKHOUSE_PASSWORD}" ${CLICKHOUSE_URL}/?query=SHOW%20TABLES
        if [ $? -eq 0 ]
        then
            echo "clickhouse is live"
            break
        fi
        sleep 2
    done
fi

#
#
#
# Ensure that the case of unset REDIS_URL is handled.
if [ ! -z "${REDIS_URL:-}" ]
then
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
fi
