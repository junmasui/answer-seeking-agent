
# Read in from the top directory's secrets.env file
export $(grep -v '^#' quick_fill.secrets.env | xargs -d '\n')

# Auto-populate passwords that will never leave the local Docker environment.

if [ -z "$APPLICATION_JWT_SECRET" ]; then
    export APPLICATION_JWT_SECRET="$(openssl rand -hex 32)"
    echo -e "\n# (Auto-generated)  APPLICATION_JWT_SECRET is created thur openssl rand -hex 32" >> quick_fill.secrets.env
    echo "APPLICATION_JWT_SECRET=${APPLICATION_JWT_SECRET}" >> quick_fill.secrets.env
fi

if [ -z "$MINIO_ROOT_PASSWORD" ]; then
    export MINIO_ROOT_PASSWORD=minio_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  Minio's root account's password" >> quick_fill.secrets.env
    echo "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" >> quick_fill.secrets.env
fi
if [ -z "$BACKEND_MINIO_USER_PASSWORD" ]; then
    export BACKEND_MINIO_USER_PASSWORD=backend_minio_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  backend's Minio\n# account's password." >> quick_fill.secrets.env
    echo "BACKEND_MINIO_USER_PASSWORD=${BACKEND_MINIO_USER_PASSWORD}" >> quick_fill.secrets.env
fi
if [ -z "$LANGFUSE_MINIO_USER_PASSWORD" ]; then
    export LANGFUSE_MINIO_USER_PASSWORD=langfuse_minio_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  Langfuse's Minio account's password." >> quick_fill.secrets.env
    echo "LANGFUSE_MINIO_USER_PASSWORD=${LANGFUSE_MINIO_USER_PASSWORD}" >> quick_fill.secrets.env
fi
export LANGFUSE_MINIO_USER_PASSWORD_ENCODED=$( echo -n $LANGFUSE_MINIO_USER_PASSWORD | jq -sRr '@uri' )


if [ -z "$POSTGRES_PASSWORD" ]; then
    export POSTGRES_PASSWORD="postgres_$(gpg --gen-random --armor 1 16)"
    echo -e "\n# (Auto-generated)  POSTGRES_PASSWORD contains Postgres's root account's password" >> quick_fill.secrets.env
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> quick_fill.secrets.env
fi
if [ -z "$BACKEND_POSTGRES_USER_PASSWORD" ]; then
    export BACKEND_POSTGRES_USER_PASSWORD="backend_postgres_$(gpg --gen-random --armor 1 16)"
    echo -e "\n# (Auto-generated)  backend's Postgres account's password." >> quick_fill.secrets.env
    echo "BACKEND_POSTGRES_USER_PASSWORD=${BACKEND_POSTGRES_USER_PASSWORD}" >> quick_fill.secrets.env
fi
if [ -z "$LANGFUSE_POSTGRES_USER_PASSWORD" ]; then
    export LANGFUSE_POSTGRES_USER_PASSWORD="langfuse_postgres_$(gpg --gen-random --armor 1 16)"
    echo -e "\n# (Auto-generated)  Langfuse's Postgres account's password." >> quick_fill.secrets.env
    echo "LANGFUSE_POSTGRES_USER_PASSWORD=${LANGFUSE_POSTGRES_USER_PASSWORD}" >> quick_fill.secrets.env
fi
export LANGFUSE_POSTGRES_USER_PASSWORD_ENCODED=$( echo -n $LANGFUSE_POSTGRES_USER_PASSWORD | jq -sRr '@uri' )

if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    export GRAFANA_ADMIN_PASSWORD=grafana_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  Grafrana's admin account's password" >> quick_fill.secrets.env
    echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}" >> quick_fill.secrets.env
fi

if [ -z "$CLICKHOUSE_DEFAULT_USER_PASSWORD" ]; then
    export CLICKHOUSE_DEFAULT_USER_PASSWORD=clickhouse_default_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  Clickhouse's default account's password" >> quick_fill.secrets.env
    echo "CLICKHOUSE_DEFAULT_USER_PASSWORD=${CLICKHOUSE_DEFAULT_USER_PASSWORD}" >> quick_fill.secrets.env
fi

if [ -z "$CLICKHOUSE_ADMIN_USER_PASSWORD" ]; then
    export CLICKHOUSE_ADMIN_USER_PASSWORD=clickhouse_admin_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  Clickhouse's admin account's password" >> quick_fill.secrets.env
    echo "CLICKHOUSE_ADMIN_USER_PASSWORD=${CLICKHOUSE_ADMIN_USER_PASSWORD}" >> quick_fill.secrets.env
fi

if [ -z "$LANGFUSE_CLICKHOUSE_USER_PASSWORD" ]; then
    export LANGFUSE_CLICKHOUSE_USER_PASSWORD=backend_clickhouse_$(gpg --gen-random --armor 1 16)
    echo -e "\n# (Auto-generated)  backend's Clickhouse\n# account's password." >> quick_fill.secrets.env
    echo "LANGFUSE_CLICKHOUSE_USER_PASSWORD=${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" >> quick_fill.secrets.env
fi
export LANGFUSE_CLICKHOUSE_USER_PASSWORD_ENCODED=$( echo -n $LANGFUSE_CLICKHOUSE_USER_PASSWORD | jq -sRr '@uri' )

if [ -z "$LANGFUSE_SALT" ]; then
    export LANGFUSE_SALT=$(openssl rand -base64 32)
    echo -e "\n# (Auto-generated)  LANGFUSE_SALT contains langfuse's salt." >> quick_fill.secrets.env
    echo "LANGFUSE_SALT=${LANGFUSE_SALT}" >> quick_fill.secrets.env
fi
if [ -z "$LANGFUSE_ENCRYPTION_KEY" ]; then
    export LANGFUSE_ENCRYPTION_KEY=$(openssl rand -hex 32)
    echo -e "\n# (Auto-generated)  LANGFUSE_ENCRYPTION_KEY contains langfuse's encryption key." >> quick_fill.secrets.env
    echo "LANGFUSE_ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}" >> quick_fill.secrets.env
fi

if [ -z "$LANGFUSE_INIT_USER_PASSWORD" ]; then
    export LANGFUSE_INIT_USER_PASSWORD=lf_pw_$(openssl rand -hex 8)
    echo -e "\n# (Auto-generated)  langfuse's initial users's password." >> quick_fill.secrets.env
    echo "LANGFUSE_INIT_USER_PASSWORD=${LANGFUSE_INIT_USER_PASSWORD}" >> quick_fill.secrets.env
fi
if [ -z "$LANGFUSE_INIT_PROJECT_SECRET_KEY" ]; then
    export LANGFUSE_INIT_PROJECT_SECRET_KEY=lf_sk_$(openssl rand -hex 8)
    echo -e "\n# (Auto-generated)  langfuse's initial project's secret key." >> quick_fill.secrets.env
    echo "LANGFUSE_INIT_PROJECT_SECRET_KEY=${LANGFUSE_INIT_PROJECT_SECRET_KEY}" >> quick_fill.secrets.env
fi
if [ -z "$LANGFUSE_INIT_PROJECT_PUBLIC_KEY" ]; then
    export LANGFUSE_INIT_PROJECT_PUBLIC_KEY=lf_pk_$(openssl rand -hex 8)
    echo -e "\n# # (Auto-generated)  langfuse's initial project's public key." >> quick_fill.secrets.env
    echo "LANGFUSE_INIT_PROJECT_PUBLIC_KEY=${LANGFUSE_INIT_PROJECT_PUBLIC_KEY}" >> quick_fill.secrets.env
fi


# Generate the services' .secrets.env

for RELPATH in "backend/backend.secrets.env" \
               "clickhouse/admin-user.xml" \
               "clickhouse/clickhouse-init.secrets.env" \
               "grafana/grafana.secrets.env" \
               "langfuse/langfuse.secrets.env" \
               "langfuse/langfuse-web.secrets.env" \
               "minio/minio-init.secrets.env" \
               "minio/minio.secrets.env" \
               "postgres/pgvector-init.secrets.env" \
               "postgres/pgvector.secrets.env"
do
    ( envsubst < ${RELPATH}.template > ${RELPATH} )
done
