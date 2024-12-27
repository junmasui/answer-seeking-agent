
# Read in from the top directory's secrets.env file
export $(grep -v '^#' quick_fill.secrets.env | xargs -d '\n')

# Auto-populate passwords that will never leave the local Docker environment.
if [ -z "$MINIO_ROOT_PASSWORD" ]; then
    export MINIO_ROOT_PASSWORD=minio_$(gpg --gen-random --armor 1 16)
fi
if [ -z "$BACKEND_MINIO_USER_PASSWORD" ]; then
    export BACKEND_MINIO_USER_PASSWORD=backend_minio_$(gpg --gen-random --armor 1 16)
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    export POSTGRES_PASSWORD="postgres_$(gpg --gen-random --armor 1 16)"
fi
if [ -z "$BACKEND_POSTGRES_USER_PASSWORD" ]; then
    export BACKEND_POSTGRES_USER_PASSWORD="backend_postgres_$(gpg --gen-random --armor 1 16)"
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
