MESSAGE="$1"

if [ -z "${MESSAGE:-}" ]
then
    echo "alembic revision MESSAGE missing"
    exit 1
fi

# Set environment variables from mounted secrets files.
# This mounting is a temporary measure, until the global configuration module
# can be made more flexible.

set +o history # temporarily turn off history
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_env | xargs -n1 )
set -o history # turn it back on

set +o history # temporarily turn off history
export REDIS_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

export POSTGRES_ANSWERS_CONNECTION_URL="postgresql+psycopg://${ANSWERS_POSTGRES_USER_NAME}:${ANSWERS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_VECTORS_CONNECTION_URL="postgresql+psycopg://${VECTORS_POSTGRES_USER_NAME}:${VECTORS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://${CHECKPOINTS_POSTGRES_USER_NAME}:${CHECKPOINTS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
set -o history # turn it back on


source .venv/bin/activate

# alembic revision [-h] [-m MESSAGE] [--autogenerate] [--sql] [--head HEAD]
#    [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH]
#    [--rev-id REV_ID] [--depends-on DEPENDS_ON]

# See https://alembic.sqlalchemy.org/en/latest/autogenerate.html#auto-generating-migrations
# Also see https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#postgresql-schema-reflection

PYTHONPATH=./src alembic revision --autogenerate -m "$MESSAGE"
