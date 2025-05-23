#!/usr/bin/env sh

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
## set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

## set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# The langfuse image is based on Alpine.
# Hence we need to use a pure-shell alternative to our more frequent technique
# of `export $( grep | xargs )`

for FILE in "${SECRETS_MOUNT}"/*_env
do
    [ -f "$FILE" ] || continue
    exec 3< "$FILE" # Open file descriptor 3. This robustly avoids subshell issues.
    while IFS='=' read -r KEY VALUE <&3  # Read from file descriptor 3.
    do
        case "$KEY" in
            # Skips comments and empty lines.
            \#* | '') continue ;;
            # Sets environment variables.
            *) export "$KEY=$VALUE" ;;
        esac
    done
    exec 3<&- # Close file descriptor 3.
done
## set -o history # turn it back on
    
# Wait for dependency-gate to open.
#

. /wait_for_gate.sh

wait_for_dependency_gate /init-signal/langfuse-gate


# Wait for web server to be ready
#
WAIT_LIMIT=300
WAIT_INTERVAL=5
ELAPSED=0

echo "Waiting for Langfuse web server to be ready..."
until [ $ELAPSED -ge $WAIT_LIMIT ]
do
    sleep $WAIT_INTERVAL
    # The $((...)) syntax is for shell arithematic operations.
    ELAPSED=$(( ELAPSED + WAIT_INTERVAL ))
    ( wget -qS -O - http://langfuse-web:3000/api/public/ready 2>&1 ) \
            | grep -q 'HTTP/1.1 200 OK'
    if [ $? == 0 ]
    then
        echo "Langfuse web server started."
        break
    fi
done

if [ $ELAPSED -ge $WAIT_LIMIT ]; then
  echo "Langfuse web server did not start within ${WAIT_LIMIT} seconds."
  exit 1
fi



export DATABASE_URL="postgres://langfuse:${LANGFUSE_POSTGRES_USER_PASSWORD}@pgvector:5432/langfuse"
export DIRECT_URL="postgres://langfuse:${LANGFUSE_POSTGRES_USER_PASSWORD}@pgvector:5432/langfuse"

export SALT="${LANGFUSE_SALT}"
export ENCRYPTION_KEY="${LANGFUSE_ENCRYPTION_KEY}"

export CLICKHOUSE_PASSWORD="${LANGFUSE_CLICKHOUSE_USER_PASSWORD}"

export LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY="${LANGFUSE_MINIO_USER_PASSWORD}"
export LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY="${LANGFUSE_MINIO_USER_PASSWORD}"

export REDIS_CONNECTION_STRING="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect langfuse/langfuse-worker:3.24 | jq '.[0].Config.Entrypoint'
exec ./worker/entrypoint.sh "$@"
