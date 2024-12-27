
# Read in from the top directory's secrets.env file
export $(grep -v '^#' quick_fill.secrets.env | xargs -d '\n')

# Auto-populate passwords that will never leave the local Docker environment.
if [ -z "$MINIO_ROOT_PASSWORD" ]; then
    export MINIO_ROOT_PASSWORD=miniopass_123
fi
if [ -z "$BACKEND_MINIO_USER_PASSWORD" ]; then
    export BACKEND_MINIO_USER_PASSWORD=backendpass_123
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    export POSTGRES_PASSWORD=postgrespass
fi
if [ -z "$BACKEND_POSTGRES_USER_PASSWORD" ]; then
    export BACKEND_POSTGRES_USER_PASSWORD=langchainpass
fi

# Generate the services' .secrets.env

for RELPATH in "backend/backend.secrets.env" \
               "minio/minio-init.secrets.env" \
               "minio/minio.secrets.env" \
               "postgres/pgvector-init.secrets.env" \
               "postgres/pgvector.secrets.env"
do
    ( envsubst < ${RELPATH}.template > ${RELPATH} )
done
