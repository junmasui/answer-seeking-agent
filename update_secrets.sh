#!/usr/bin/env bash

##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

[ ! -d ./secrets ] && mkdir ./secrets

# Generate the manually managed secrets file.
if [ ! -e secrets-dev.env ]
then
    HF_TOKEN="${HF_TOKEN:-$HUGGINGFACEHUB_API_TOKEN}" \
       HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN:-$HF_TOKEN}" \
       envsubst < ./secrets.env.template > ./secrets-dev.env
fi

# Generate the manually managed secrets file.
if [ ! -e secrets-test.env ]
then
    HF_TOKEN="${HF_TOKEN:-$HUGGINGFACEHUB_API_TOKEN}" \
       HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN:-$HF_TOKEN}" \
       envsubst < ./secrets.env.template > ./secrets-test.env
fi


# Generate TLS keys for clickhouse
#

if [[ ! -e ./secrets/clickhouse.server.crt \
    || ! -e ./secrets/clickhouse.server.key ]]
then
    openssl req -subj "/CN=localhost" -new -newkey rsa:2048 -days 365 -nodes -x509 \
        -keyout ./secrets/clickhouse.server.key -out ./secrets/clickhouse.server.crt

    chmod ug=rw secrets/clickhouse.server.crt
    chmod ug=rw secrets/clickhouse.server.key

    sudo chown rootless-101:rootless-101  secrets/clickhouse.server.crt
    sudo chown rootless-101:rootless-101  secrets/clickhouse.server.key
fi



# Auto-generate passwords that will never leave the local Docker environment.

function generate_secret ()  {
    SECRETS_FILE="$1"
    VAR_NAME="$2"
    ALGO="$3"
    PREFIX="$4"
    DESCR="$5"
    if [[ ! -e "$SECRETS_FILE" \
        || ! $( grep "$VAR_NAME" "$SECRETS_FILE" ) ]]
    then
        if [ -z "${!VAR_NAME:-}" ]
        then
            case "$ALGO" in
                "gpg-16-safe" )
                    SECRET=$( gpg --gen-random --armour 1 16 | tr '+/' '-_' | tr -d '=' ) ;;
                "gpg-32-safe" )
                    SECRET=$( gpg --gen-random --armour 1 32 | tr '+/' '-_' | tr -d '=' ) ;;
                "openssl-8" )
                    SECRET=$( openssl rand -hex 8 ) ;;
                "openssl-32" )
                    SECRET=$( openssl rand -hex 32 ) ;;
                "openssl-32-safe" )
                    SECRET=$( openssl rand -hex 32 | tr '+/' '-_' | tr -d '='  ) ;;
                "uuidgen" )
                    SECRET=$( uuidgen ) ;;
                * )
                    echo "Unknown algorithm $ALGO for $VAR_NAME in $SECRETS_FILE"
                    exit 1 ;;
            esac
            declare "${VAR_NAME}=${PREFIX}${SECRET}"
        fi
        echo -e "\n# ${DESCR}  (auto-generated secret)" >> "$SECRETS_FILE"
        echo "$VAR_NAME=${!VAR_NAME}" >> "$SECRETS_FILE"
    fi
}


# Answers JWT

SECRETS_FILE=./secrets/answers-dev.jwt.secrets.env
VAR_NAME=APPLICATION_JWT_SECRET
DESCR="$VAR_NAME is created thru openssl rand -hex 32."

generate_secret "$SECRETS_FILE" "$VAR_NAME" openssl-32 "" "$DESCR"

SECRETS_FILE=./secrets/answers-test.jwt.secrets.env

generate_secret "$SECRETS_FILE" "$VAR_NAME" openssl-32 "" "$DESCR"


# Celery Flower

SECRETS_FILE=./secrets/celery-flower-dev.secrets.env
VAR_NAME=CELERY_FLOWER_USER_PASSWORD
VALUE_PREFIX=celery_flower_dev_
DESCR="Celery Flower basic auth account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/celery-flower-test.secrets.env
VAR_NAME=CELERY_FLOWER_USER_PASSWORD
VALUE_PREFIX=celery_flower_test_
DESCR="Celery Flower basic auth account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Clickhouse

SECRETS_FILE=./secrets/clickhouse.secrets.env
VAR_NAME=CLICKHOUSE_DEFAULT_USER_PASSWORD
VALUE_PREFIX=clickhouse_default_
DESCR="Clickhouse's default account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

VAR_NAME=CLICKHOUSE_ADMIN_USER_PASSWORD
VALUE_PREFIX=clickhouse_admin_
DESCR="Clickhouse's admin account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/langfuse.clickhouse.secrets.env
VAR_NAME=LANGFUSE_CLICKHOUSE_USER_PASSWORD
VALUE_PREFIX=langfuse_clickhouse_
DESCR="Langfuse's Clickhouse account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"



# Grafana

SECRETS_FILE=./secrets/grafana.secrets.env
VAR_NAME=GRAFANA_ADMIN_PASSWORD
VALUE_PREFIX=grafana_
DESCR="Grafrana's admin account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"



# Langfuse

SECRETS_FILE=./secrets/langfuse.secrets.env
VAR_NAME=LANGFUSE_SALT
DESCR="LANGFUSE_SALT contains langfuse's salt."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "openssl-32-safe" "" "$DESCR"

VAR_NAME=LANGFUSE_ENCRYPTION_KEY
DESCR="LANGFUSE_ENCRYPTION_KEY contains langfuse's encryption key."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "openssl-32-safe" "" "$DESCR"


# Langfuse-web

SECRETS_FILE=./secrets/langfuse-web.secrets.env
VAR_NAME=LANGFUSE_INIT_USER_PASSWORD
VALUE_PREFIX=lf_pw_
DESCR="langfuse's initial users's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "openssl-8" "$VALUE_PREFIX" "$DESCR"

VAR_NAME=LANGFUSE_INIT_PROJECT_SECRET_KEY
VALUE_PREFIX=sk-lf-
DESCR="langfuse's initial users's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "uuidgen" "$VALUE_PREFIX" "$DESCR"

VAR_NAME=LANGFUSE_INIT_PROJECT_PUBLIC_KEY
VALUE_PREFIX=pk-lf-
DESCR="langfuse's initial users's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "uuidgen" "$VALUE_PREFIX" "$DESCR"


# Minio

SECRETS_FILE=./secrets/minio.secrets.env
VAR_NAME=MINIO_ROOT_PASSWORD
VALUE_PREFIX=minio_
DESCR="Minio's root account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/answers-dev.minio.secrets.env
VAR_NAME=ANSWERS_MINIO_USER_PASSWORD
VALUE_PREFIX=backend_minio_
DESCR="Backend's Minio account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/answers-test.minio.secrets.env
VALUE_PREFIX=backend_test_minio_
DESCR="Backend Test's Minio account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/langfuse.minio.secrets.env
VAR_NAME=LANGFUSE_MINIO_USER_PASSWORD
VALUE_PREFIX=langfuse_minio_
DESCR="Langfuse's Minio account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Postgres


SECRETS_FILE=./secrets/postgres.secrets.env
VAR_NAME=POSTGRES_PASSWORD
VALUE_PREFIX=postgres_
DESCR="Postgres's root account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/answers-dev.postgres.secrets.env
VAR_NAME=BACKEND_ANSWERS_POSTGRES_USER_PASSWORD
VALUE_PREFIX=answers_postgres_
DESCR="backend's Answers Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/answers-test.postgres.secrets.env
VALUE_PREFIX=answers_test_postgres_
DESCR="backend test's Answers Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/checkpoints-dev.postgres.secrets.env
VAR_NAME=BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD
VALUE_PREFIX=checkpoints_postgres_
DESCR="backend's checkpoints Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/checkpoints-test.postgres.secrets.env
VALUE_PREFIX=checkpoints_test_postgres_
DESCR="backend test's checkpoints Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/vectors-dev.postgres.secrets.env
VAR_NAME=BACKEND_VECTORS_POSTGRES_USER_PASSWORD
VALUE_PREFIX=vectors_postgres_
DESCR="backend's vectors Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/vectors-test.postgres.secrets.env
VALUE_PREFIX=vectors_test_postgres_
DESCR="backend test's vectors Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"




SECRETS_FILE=./secrets/langfuse.postgres.secrets.env
VAR_NAME=LANGFUSE_POSTGRES_USER_PASSWORD
VALUE_PREFIX=langfuse_postgres_
DESCR="Langfuse's Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Redis

SECRETS_FILE=./secrets/redis.secrets.env
VAR_NAME=REDIS_DEFAULT_PASSWORD
VALUE_PREFIX=redis_
DESCR="Redis's default account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

# Weaviate

SECRETS_FILE=./secrets/weaviate.secrets.env
VAR_NAME=WEAVIATE_USER_API_KEY
VALUE_PREFIX=weaviate_
DESCR="Weaviate's default account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


#=======

#
set +o history # temporarily turn off history
# shellcheck disable=SC2046
export $( grep -h -v "^#" "./secrets/clickhouse.secrets.env" | xargs -n1 )

set -o history # turn it back on

RELPATH=clickhouse/admin-user.xml
envsubst < "${RELPATH}.template" > "secrets/clickhouse.admin-user.xml"

#
set +o history # temporarily turn off history
# shellcheck disable=SC2046
export $( grep -h -v "^#" "./secrets/redis.secrets.env" | xargs -n1 )

set -o history # turn it back on

RELPATH=redis/redis.conf
envsubst < "${RELPATH}.template" > "secrets/redis.conf"
