#!/usr/bin/env bash

##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

[ ! -d ./secrets ] && mkdir ./secrets

# Generate the manually managed secrets file.
if [ ! -e secrets.env ]
then
    HF_TOKEN=${HF_TOKEN:-$HUGGINGFACEHUB_API_TOKEN} \
       HUGGINGFACEHUB_API_TOKEN=${HUGGINGFACEHUB_API_TOKEN:-$HF_TOKEN} \
       envsubst < ./secrets.env.template > ./secrets.env
fi

# Read from the top directory's autogren secrets.env file
export $(grep -h -v '^#' secrets-autogen.env | xargs -d '\n')

# Read from .secrets.env files in the secrets directory.
export $(grep -h -v '^#' secrets/*.secrets.env | xargs -d '\n')

# Generate TLS keys for clickhouse
#

if [[ ! -e ./secrets/clickhouse.server.crt \
    || ! -e ./secrets/clickhouse.server.key ]]
then
    openssl req -subj "/CN=localhost" -new -newkey rsa:2048 -days 365 -nodes -x509 \
        -keyout ./secrets/clickhouse.server.key -out ./secrets/clickhouse/server.crt
fi



# Auto-generate passwords that will never leave the local Docker environment.


# Answers JWT

SECRETS_FILE=./secrets/answers.jwt.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep APPLICATION_JWT_SECRET $SECRETS_FILE ) ]]
then
    if [ -z "$APPLICATION_JWT_SECRET" ]
    then
        export APPLICATION_JWT_SECRET="$(openssl rand -hex 32)"
    fi
    echo -e "\n# APPLICATION_JWT_SECRET is created thru openssl rand -hex 32.  (auto-generated secret)" >> $SECRETS_FILE
    echo "APPLICATION_JWT_SECRET=${APPLICATION_JWT_SECRET}" >> $SECRETS_FILE
fi


# Clickhouse
SECRETS_FILE=./secrets/clickhouse.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep CLICKHOUSE_DEFAULT_USER_PASSWORD $SECRETS_FILE ) \
      || ! $( grep CLICKHOUSE_ADMIN_USER_PASSWORD $SECRETS_FILE )  ]]
then
    if [ -z "$CLICKHOUSE_DEFAULT_USER_PASSWORD" ]
    then
        export CLICKHOUSE_DEFAULT_USER_PASSWORD=clickhouse_default_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# Clickhouse's default account's password  (auto-generated secret)" >> $SECRETS_FILE
    echo "CLICKHOUSE_DEFAULT_USER_PASSWORD=${CLICKHOUSE_DEFAULT_USER_PASSWORD}" >> $SECRETS_FILE

    if [ -z "$CLICKHOUSE_ADMIN_USER_PASSWORD" ]
    then
        export CLICKHOUSE_ADMIN_USER_PASSWORD=clickhouse_admin_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# Clickhouse's admin account's password  (auto-generated secret)" >> $SECRETS_FILE
    echo "CLICKHOUSE_ADMIN_USER_PASSWORD=${CLICKHOUSE_ADMIN_USER_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/langfuse.clickhouse.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep LANGFUSE_CLICKHOUSE_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$LANGFUSE_CLICKHOUSE_USER_PASSWORD" ]; then
        export LANGFUSE_CLICKHOUSE_USER_PASSWORD=langfuse_clickhouse_$(gpg --gen-random --armour 1 16| tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# backend's Clickhouse account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_CLICKHOUSE_USER_PASSWORD=${LANGFUSE_CLICKHOUSE_USER_PASSWORD}" >> $SECRETS_FILE
fi


# Grafana

SECRETS_FILE=./secrets/grafana.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep GRAFANA_ADMIN_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
        export GRAFANA_ADMIN_PASSWORD=grafana_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# Grafrana's admin account's password  (auto-generated secret)" >> $SECRETS_FILE
    echo "GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}" >> $SECRETS_FILE
    echo "GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}" >> $SECRETS_FILE
fi

# Langfuse

SECRETS_FILE=./secrets/langfuse.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep LANGFUSE_SALT $SECRETS_FILE ) \
      || ! $( grep LANGFUSE_ENCRYPTION_KEY $SECRETS_FILE ) ]]
then
    if [ -z "$LANGFUSE_SALT" ]; then
        export LANGFUSE_SALT=$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# LANGFUSE_SALT contains langfuse's salt.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_SALT=${LANGFUSE_SALT}" >> $SECRETS_FILE

    if [ -z "$LANGFUSE_ENCRYPTION_KEY" ]; then
        export LANGFUSE_ENCRYPTION_KEY=$(openssl rand -hex 32)
    fi
    echo -e "\n# LANGFUSE_ENCRYPTION_KEY contains langfuse's encryption key.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_ENCRYPTION_KEY=${LANGFUSE_ENCRYPTION_KEY}" >> $SECRETS_FILE
fi

# Langfuse-web

SECRETS_FILE=./secrets/langfuse-web.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep LANGFUSE_INIT_USER_PASSWORD $SECRETS_FILE ) \
      || ! $( grep LANGFUSE_INIT_PROJECT_SECRET_KEY $SECRETS_FILE ) \
      || ! $( grep LANGFUSE_INIT_PROJECT_PUBLIC_KEY $SECRETS_FILE ) ]]
then
    if [ -z "$LANGFUSE_INIT_USER_PASSWORD" ]; then
        export LANGFUSE_INIT_USER_PASSWORD=lf_pw_$(openssl rand -hex 8)
    fi
    echo -e "\n# langfuse's initial users's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_INIT_USER_PASSWORD=${LANGFUSE_INIT_USER_PASSWORD}" >> $SECRETS_FILE

    if [ -z "$LANGFUSE_INIT_PROJECT_SECRET_KEY" ]; then
        export LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-$( uuidgen )
    fi
    echo -e "\n# langfuse's initial project's secret key.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_INIT_PROJECT_SECRET_KEY=${LANGFUSE_INIT_PROJECT_SECRET_KEY}" >> $SECRETS_FILE

    if [ -z "$LANGFUSE_INIT_PROJECT_PUBLIC_KEY" ]; then
        export LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-$( uuidgen )
    fi
    echo -e "\n# # langfuse's initial project's public key.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_INIT_PROJECT_PUBLIC_KEY=${LANGFUSE_INIT_PROJECT_PUBLIC_KEY}" >> $SECRETS_FILE
fi

# Minio
SECRETS_FILE=./secrets/minio.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep MINIO_ROOT_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$MINIO_ROOT_PASSWORD" ]; then
        export MINIO_ROOT_PASSWORD=minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# Minio's root account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/answers.minio.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep BACKEND_MINIO_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$BACKEND_MINIO_USER_PASSWORD" ]; then
        export BACKEND_MINIO_USER_PASSWORD=backend_minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# backend's Minio\n# account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "BACKEND_MINIO_USER_PASSWORD=${BACKEND_MINIO_USER_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/langfuse.minio.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep LANGFUSE_MINIO_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$LANGFUSE_MINIO_USER_PASSWORD" ]; then
        export LANGFUSE_MINIO_USER_PASSWORD=langfuse_minio_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')
    fi
    echo -e "\n# Langfuse's Minio account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_MINIO_USER_PASSWORD=${LANGFUSE_MINIO_USER_PASSWORD}" >> $SECRETS_FILE
fi

# Postgres
SECRETS_FILE=./secrets/postgres.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep POSTGRES_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$POSTGRES_PASSWORD" ]; then
        export POSTGRES_PASSWORD="postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# POSTGRES_PASSWORD contains Postgres's root account's password  (auto-generated secret)" >> $SECRETS_FILE
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/answers.postgres.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep BACKEND_POSTGRES_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$BACKEND_POSTGRES_USER_PASSWORD" ]; then
        export BACKEND_POSTGRES_USER_PASSWORD="backend_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# backend's Postgres account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "BACKEND_POSTGRES_USER_PASSWORD=${BACKEND_POSTGRES_USER_PASSWORD}" >> $SECRETS_FILE
fi


SECRETS_FILE=./secrets/checkpoints.postgres.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD" ]; then
        export BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD="backend_checkpoints_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# backend checkpointer's Postgres account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD=${BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/vectors.postgres.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep BACKEND_VECTORS_POSTGRES_USER_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$BACKEND_VECTORS_POSTGRES_USER_PASSWORD" ]; then
        export BACKEND_VECTORS_POSTGRES_USER_PASSWORD="backend_vectors_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# backend vector stores's Postgres account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "BACKEND_VECTORS_POSTGRES_USER_PASSWORD=${BACKEND_VECTORS_POSTGRES_USER_PASSWORD}" >> $SECRETS_FILE
fi

SECRETS_FILE=./secrets/langfuse.postgres.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep LANGFUSE_POSTGRES_USER_PASSWORD $SECRETS_FILE ) \
      || ! $( grep LANGFUSE_POSTGRES_DATABASE_URL $SECRETS_FILE ) ]]
then
    if [ -z "$LANGFUSE_POSTGRES_USER_PASSWORD" ]; then
        export LANGFUSE_POSTGRES_USER_PASSWORD="langfuse_postgres_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# Langfuse's Postgres account's password.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_POSTGRES_USER_PASSWORD=${LANGFUSE_POSTGRES_USER_PASSWORD}" >> $SECRETS_FILE

    echo -e "\n# Langfuse's Database URL.  (auto-generated secret)" >> $SECRETS_FILE
    echo "LANGFUSE_POSTGRES_DATABASE_URL=postgres://langfuse:${LANGFUSE_POSTGRES_USER_PASSWORD}@pgvector:5432/langfuse" >> $SECRETS_FILE
fi


# Redis
SECRETS_FILE=./secrets/redis.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep REDIS_DEFAULT_PASSWORD $SECRETS_FILE ) ]]
then
    if [ -z "$REDIS_DEFAULT_PASSWORD" ]
    then
        export REDIS_DEFAULT_PASSWORD="redis_$(gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=')"
    fi
    echo -e "\n# REDIS_DEFAULT_PASSWORD contains Redis's default account's password  (auto-generated secret)" >> $SECRETS_FILE
    echo "REDIS_DEFAULT_PASSWORD=${REDIS_DEFAULT_PASSWORD}" >> $SECRETS_FILE

    echo -e "\n# REDIS_URL contains the URL with Redis's default account and password  (auto-generated secret)" >> $SECRETS_FILE
    echo "REDIS_URL=redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0" >> $SECRETS_FILE
fi



#=======

# Celery-exporter depends on Redis password
SECRETS_FILE=./secrets/celery-exporter.secrets.env
if [[ ! -e $SECRETS_FILE \
      || ! $( grep CE_BROKER_URL $SECRETS_FILE ) ]]
then
    echo "CE_BROKER_URL=redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0" >> $SECRETS_FILE
fi

#
RELPATH=clickhouse/admin-user.xml
envsubst < ${RELPATH}.template > secrets/clickhouse.admin-user.xml

#
RELPATH=redis/redis.conf
envsubst < ${RELPATH}.template > secrets/redis.conf
