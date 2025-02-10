#!/bin/sh

# See the original entrypoint that we are replacing:
# https://github.com/langfuse/langfuse/blob/main/worker/Dockerfile#L76

set -u
set -x

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

#
# Wait for DNS resolution of minio, postgres, clickhouse, and redis
#
for TARGET_HOST in minio pgvector clickhouse redis
do
    while true
    do
        # Hmm.. We need to add the non-authoritative DNS server explicitly
        # even though it is declared in /etc/resolv.conf
        nslookup $TARGET_HOST 127.0.0.11
        if [ $? -eq 0 ]
        then
            echo "DNS name ${TARGET_HOST} resolves"
            break
        fi
        sleep 2
    done
done

#
# Wait for minio to be ready
#
echo "Waiting for minio to be ready"
while true
do
    curl -f ${LANGFUSE_S3_EVENT_UPLOAD_ENDPOINT}/minio/health/live
    if [ $? -eq 0 ]
    then
        echo "minio is live"
        break
    fi
    sleep 2
done

# #
# # Wait for postgres to be ready
# #
# echo "Waiting for postgres to be ready"
# while true
# do
#     pg_isready -d "${DATABASE_URL}"
#     if [ $? -eq 0 ]
#     then
#         echo "postgres is ready"
#         break
#     fi
#     sleep 2
# done

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

#
# Launch the original langfuse-worker entrypoint
#
exec /app/worker/entrypoint.sh "$@"
