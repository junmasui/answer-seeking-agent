#!/usr/bin/env bash

##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

[ ! -d ./secrets ] && mkdir ./secrets

HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN:-}"
export HF_TOKEN="${HF_TOKEN:-$HUGGINGFACEHUB_API_TOKEN}"
export HUGGINGFACEHUB_API_TOKEN="${HUGGINGFACEHUB_API_TOKEN:-$HF_TOKEN}"

# Generate the manually managed secrets file.
if [ ! -e secrets.env ]
then
    envsubst < ./secrets.env.template > ./secrets.env
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

SECRETS_FILE=./secrets/answers.jwt.secrets.env
VAR_NAME=APPLICATION_JWT_SECRET
DESCR="$VAR_NAME is created thru openssl rand -hex 32."

generate_secret "$SECRETS_FILE" "$VAR_NAME" openssl-32 "" "$DESCR"

SECRETS_FILE=./secrets/answers.jwt.autotest.secrets.env

generate_secret "$SECRETS_FILE" "$VAR_NAME" openssl-32 "" "$DESCR"


# Answers API keys

SECRETS_FILE=./secrets/answers.api-key.secrets.env
VAR_NAME=APPLICATION_API_KEY_1
VALUE_PREFIX=answers_1_
DESCR="Answers API key."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/answers.api-key.autotest.secrets.env
VALUE_PREFIX=answers_dev_1_

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

VAR_NAME=APPLICATION_API_KEY_2
VALUE_PREFIX=answers_dev_2_

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

VAR_NAME=APPLICATION_API_KEY_3
VALUE_PREFIX=answers_dev_3_

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

# Celery Flower

SECRETS_FILE=./secrets/celery-flower.secrets.env
VAR_NAME=CELERY_FLOWER_USER_PASSWORD
VALUE_PREFIX=celery_flower_
DESCR="Celery Flower basic auth account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/celery-flower.autotest.secrets.env
VAR_NAME=CELERY_FLOWER_USER_PASSWORD
VALUE_PREFIX=celery_flower_dev_
DESCR="Celery Flower basic auth account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Grafana

SECRETS_FILE=./secrets/grafana.secrets.env
VAR_NAME=GRAFANA_ADMIN_PASSWORD
VALUE_PREFIX=grafana_
DESCR="Grafrana's admin account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"



# Seaweed

SECRETS_FILE=./secrets/seaweedfs.secrets.env
VAR_NAME=SEAWEEDFS_ROOT_PASSWORD
VALUE_PREFIX=seaweedfs_
DESCR="seaweedfs's root account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/answers.seaweedfs.secrets.env
VAR_NAME=S3_SECRET_KEY
VALUE_PREFIX=backend_seaweedfs_
DESCR="Backend's seaweedfs account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/answers.seaweedfs.autotest.secrets.env
VALUE_PREFIX=backend_seaweedfs_dev_
DESCR="Backend Test's seaweedfs account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/codebase.seaweedfs.secrets.env
VAR_NAME=CODEBASE_SECRET_KEY
VALUE_PREFIX=codebase_seaweedfs_
DESCR="Codebase bucket's secret key."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-32-safe" "$VALUE_PREFIX" "$DESCR"


# Postgres


SECRETS_FILE=./secrets/postgres.secrets.env
VAR_NAME=POSTGRES_PASSWORD
VALUE_PREFIX=postgres_
DESCR="Postgres's root account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/answers.postgres.secrets.env
VAR_NAME=ANSWERS_POSTGRES_USER_PASSWORD
VALUE_PREFIX=answers_postgres_
DESCR="backend's Answers Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/answers.postgres.autotest.secrets.env
VALUE_PREFIX=answers_postgres_dev_
DESCR="backend test's Answers Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


SECRETS_FILE=./secrets/checkpoints.postgres.secrets.env
VAR_NAME=CHECKPOINTS_POSTGRES_USER_PASSWORD
VALUE_PREFIX=checkpoints_postgres_
DESCR="backend's checkpoints Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

SECRETS_FILE=./secrets/checkpoints.postgres.autotest.secrets.env
VALUE_PREFIX=checkpoints_postgres_dev_
DESCR="backend test's checkpoints Postgres account's password."

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


# OpenSearch
SECRETS_FILE=./secrets/opensearch.secrets.env
VAR_NAME=OPENSEARCH_INITIAL_ADMIN_PASSWORD
VALUE_PREFIX=opensearch_admin_
DESCR="OpenSearch's initial admin password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# MLflow Postgres
SECRETS_FILE=./secrets/mlflow.postgres.secrets.env
VAR_NAME=MLFLOW_POSTGRES_USER_PASSWORD
VALUE_PREFIX=mlflow_postgres_
DESCR="MLflow Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

# MLflow SeaweedFS
SECRETS_FILE=./secrets/mlflow.seaweedfs.secrets.env
VAR_NAME=S3_SECRET_KEY
VALUE_PREFIX=mlflow_seaweedfs_
DESCR="MLflow's seaweedfs account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Keycloak Postgres
SECRETS_FILE=./secrets/keycloak.postgres.secrets.env
VAR_NAME=KEYCLOAK_POSTGRES_USER_PASSWORD
VALUE_PREFIX=keycloak_postgres_
DESCR="Keycloak Postgres account's password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"

# Keycloak Admin
SECRETS_FILE=./secrets/keycloak.admin.secrets.env
VAR_NAME=KEYCLOAK_ADMIN_PASSWORD
VALUE_PREFIX=keycloak_admin_
DESCR="Keycloak Admin password."

generate_secret "$SECRETS_FILE" "$VAR_NAME" "gpg-16-safe" "$VALUE_PREFIX" "$DESCR"


# Mutagen SSH keys (file-sync -> autotest services)
MUTAGEN_PRIVATE_KEY=./secrets/mutagen.private_key
MUTAGEN_AUTHORIZED_KEYS=./secrets/mutagen.authorized_keys
MUTAGEN_KEYPAIR_BASE=./secrets/mutagen_ed25519

if [ ! -f "$MUTAGEN_PRIVATE_KEY" ] || [ ! -f "$MUTAGEN_AUTHORIZED_KEYS" ]; then
    if command -v ssh-keygen >/dev/null 2>&1; then
        ssh-keygen -t ed25519 -N "" -f "$MUTAGEN_KEYPAIR_BASE" >/dev/null 2>&1
        cp "$MUTAGEN_KEYPAIR_BASE" "$MUTAGEN_PRIVATE_KEY"
        cp "${MUTAGEN_KEYPAIR_BASE}.pub" "$MUTAGEN_AUTHORIZED_KEYS"
        chmod 600 "$MUTAGEN_PRIVATE_KEY"
        chmod 644 "$MUTAGEN_AUTHORIZED_KEYS"
    else
        echo "ssh-keygen not found. Skipping Mutagen SSH key generation."
    fi
fi
