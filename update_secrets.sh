#!/usr/bin/env bash


# If 
if [ ! -e secrets.env ]; then
    HF_TOKEN=${HF_TOKEN:-$HUGGINGFACEHUB_API_TOKEN} \
    HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN:-$HF_TOKEN} \
    envsubst < secrets.env.template > secrets.env
fi

# Read in from the top directory's secrets.env file
export $(grep -v '^#' secrets.env | xargs -d '\n')

# Auto-generate passwords that will never leave the local Docker environment.

if [ -z "$APPLICATION_JWT_SECRET" ]; then
    export APPLICATION_JWT_SECRET="$(openssl rand -hex 32)"
    echo -e "\n# APPLICATION_JWT_SECRET is created thru openssl rand -hex 32.  (auto-generated secret)" >> secrets.env
    echo "APPLICATION_JWT_SECRET=${APPLICATION_JWT_SECRET}" >> secrets.env
fi

if [ -z "$MINIO_ROOT_PASSWORD" ]; then
    export MINIO_ROOT_PASSWORD=minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# Minio's root account's password.  (auto-generated secret)" >> secrets.env
    echo "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" >> secrets.env
fi
if [ -z "$BACKEND_MINIO_USER_PASSWORD" ]; then
    export BACKEND_MINIO_USER_PASSWORD=backend_minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# backend's Minio\n# account's password.  (auto-generated secret)" >> secrets.env
    echo "BACKEND_MINIO_USER_PASSWORD=${BACKEND_MINIO_USER_PASSWORD}" >> secrets.env
fi
if [ -z "$LANGFUSE_MINIO_USER_PASSWORD" ]; then
    export LANGFUSE_MINIO_USER_PASSWORD=langfuse_minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# Langfuse's Minio account's password.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_MINIO_USER_PASSWORD=${LANGFUSE_MINIO_USER_PASSWORD}" >> secrets.env
fi

if [ -z "$REDIS_DEFAULT_PASSWORD" ]; then
    export REDIS_DEFAULT_PASSWORD="redis_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    echo -e "\n# REDIS_DEFAULT_PASSWORD contains Redis's default account's password  (auto-generated secret)" >> secrets.env
    echo "REDIS_DEFAULT_PASSWORD=${REDIS_DEFAULT_PASSWORD}" >> secrets.env
fi


if [ -z "$POSTGRES_PASSWORD" ]; then
    export POSTGRES_PASSWORD="postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    echo -e "\n# POSTGRES_PASSWORD contains Postgres's root account's password  (auto-generated secret)" >> secrets.env
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> secrets.env
fi
if [ -z "$BACKEND_POSTGRES_USER_PASSWORD" ]; then
    export BACKEND_POSTGRES_USER_PASSWORD="backend_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    echo -e "\n# backend's Postgres account's password.  (auto-generated secret)" >> secrets.env
    echo "BACKEND_POSTGRES_USER_PASSWORD=${BACKEND_POSTGRES_USER_PASSWORD}" >> secrets.env
fi
if [ -z "$LANGFUSE_POSTGRES_USER_PASSWORD" ]; then
    export LANGFUSE_POSTGRES_USER_PASSWORD="langfuse_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    echo -e "\n# Langfuse's Postgres account's password.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_POSTGRES_USER_PASSWORD=${LANGFUSE_POSTGRES_USER_PASSWORD}" >> secrets.env
fi

if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    export GRAFANA_ADMIN_PASSWORD=grafana_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# Grafrana's admin account's password  (auto-generated secret)" >> secrets.env
    echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}" >> secrets.env
fi

if [ -z "$CLICKHOUSE_DEFAULT_USER_PASSWORD" ]; then
    export CLICKHOUSE_DEFAULT_USER_PASSWORD=clickhouse_default_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# Clickhouse's default account's password  (auto-generated secret)" >> secrets.env
    echo "CLICKHOUSE_DEFAULT_USER_PASSWORD=${CLICKHOUSE_DEFAULT_USER_PASSWORD}" >> secrets.env
fi

if [ -z "$CLICKHOUSE_ADMIN_USER_PASSWORD" ]; then
    export CLICKHOUSE_ADMIN_USER_PASSWORD=clickhouse_admin_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# Clickhouse's admin account's password  (auto-generated secret)" >> secrets.env
    echo "CLICKHOUSE_ADMIN_USER_PASSWORD=${CLICKHOUSE_ADMIN_USER_PASSWORD}" >> secrets.env
fi

if [ -z "$LANGFUSE_CLICKHOUSE_USER_PASSWORD" ]; then
    export LANGFUSE_CLICKHOUSE_USER_PASSWORD=langfuse_clickhouse_$(gpg --gen-random --armour 1 16| tr '+/' '-_' | tr -d '=')
    echo -e "\n# backend's Clickhouse account's password.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_CLICKHOUSE_USER_PASSWORD=${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" >> secrets.env
fi

if [ -z "$LANGFUSE_SALT" ]; then
    export LANGFUSE_SALT=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
    echo -e "\n# LANGFUSE_SALT contains langfuse's salt.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_SALT=${LANGFUSE_SALT}" >> secrets.env
fi
if [ -z "$LANGFUSE_ENCRYPTION_KEY" ]; then
    export LANGFUSE_ENCRYPTION_KEY=$(openssl rand -hex 32)
    echo -e "\n# LANGFUSE_ENCRYPTION_KEY contains langfuse's encryption key.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}" >> secrets.env
fi

if [ -z "$LANGFUSE_INIT_USER_PASSWORD" ]; then
    export LANGFUSE_INIT_USER_PASSWORD=lf_pw_$(openssl rand -hex 8)
    echo -e "\n# langfuse's initial users's password.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_INIT_USER_PASSWORD=${LANGFUSE_INIT_USER_PASSWORD}" >> secrets.env
fi
if [ -z "$LANGFUSE_INIT_PROJECT_SECRET_KEY" ]; then
    export LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-$( uuidgen )
    echo -e "\n# langfuse's initial project's secret key.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_INIT_PROJECT_SECRET_KEY=${LANGFUSE_INIT_PROJECT_SECRET_KEY}" >> secrets.env
fi
if [ -z "$LANGFUSE_INIT_PROJECT_PUBLIC_KEY" ]; then
    export LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-$( uuidgen )
    echo -e "\n# # langfuse's initial project's public key.  (auto-generated secret)" >> secrets.env
    echo "LANGFUSE_INIT_PROJECT_PUBLIC_KEY=${LANGFUSE_INIT_PROJECT_PUBLIC_KEY}" >> secrets.env
fi


# Generate the services' .secrets.env

for RELPATH in "backend/backend.secrets.env" \
               "backend/celery-exporter.secrets.env" \
               "backend/start-gate.secrets.env" \
               "clickhouse/admin-user.xml" \
               "clickhouse/clickhouse-init.secrets.env" \
               "grafana/grafana.secrets.env" \
               "langfuse/langfuse.secrets.env" \
               "langfuse/langfuse-web.secrets.env" \
               "langfuse/start-gate.secrets.env" \
               "minio/minio-init.secrets.env" \
               "minio/minio.secrets.env" \
               "postgres/pgvector-init.secrets.env" \
               "postgres/pgvector.secrets.env" \
               "redis/redis.conf"
do
    sudo chmod go+rw ${RELPATH}
    ( envsubst < ${RELPATH}.template > ${RELPATH} )
    sudo chmod o-rwx ${RELPATH}
done
