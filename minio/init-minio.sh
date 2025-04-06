
# Set environment variables from .secrets.env files
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
# The minio/minio image does not include the Debian findutil and grep packages.
# Hence we need to use a pure-shell alternative to our more frequent technique
# of `export $( grep | xargs )`
for FILE in ${SECRETS_MOUNT}/*_env
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


WAIT_LIMIT=300
WAIT_INTERVAL=5
ELAPSED=0

echo "Waiting for Minio server to be ready..."
until ( mc alias set local_server http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} \
        && mc admin info local_server ) \
      || [ $ELAPSED -ge $WAIT_LIMIT ]; do
  sleep $WAIT_INTERVAL
  # The $((...)) syntax is for shell arithematic operations.
  ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $WAIT_LIMIT ]; then
  echo "Minio server did not start within ${WAIT_LIMIT} seconds."
  exit 1
fi

#
#
#

mc mb local_server/${ANSWERS_MINIO_BUCKET}

mc admin user add local_server ${ANSWERS_MINIO_USER_NAME} ${ANSWERS_MINIO_USER_PASSWORD}

mc admin policy attach local_server readwrite --user ${ANSWERS_MINIO_USER_NAME}

