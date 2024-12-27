

WAIT_LIMIT=300
WAIT_INTERVAL=5
ELAPSED=0

echo "Waiting for Minio server to be ready..."
until ( mc alias set local_server http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && mc admin info local_server ) || [ $ELAPSED -ge $WAIT_LIMIT ]; do
  sleep $WAIT_INTERVAL
  # The $((...)) syntax is for shell arithematic operations.
  ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ $ELAPSED -ge $WAIT_LIMIT ]; then
  echo "Minio server did not start within ${WAIT_LIMIT} seconds."
  exit 1
fi


mc mb local_server/${BACKEND_MINIO_BUCKET}

mc admin user add local_server ${BACKEND_MINIO_USER_NAME} ${BACKEND_MINIO_USER_PASSWORD}

mc admin policy attach local_server readwrite --user ${BACKEND_MINIO_USER_NAME}

