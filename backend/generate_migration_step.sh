
MESSAGE=$1

if [ -z "$MESSAGE" ]
then
    echo "alembic revision MESSAGE missing"
    exit -1
fi

# Set environment variables from mounted secrets files.
# This mounting is a temporary measure, until the global configuration module
# can be made more flexible.

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
set -o history # turn it back on

set +o history # temporarily turn off history
export POSTGRES_ANSWERS_CONNECTION_URL="postgresql+psycopg://answers:${BACKEND_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_VECTORS_CONNECTION_URL="postgresql+psycopg://answers_vectors:${BACKEND_VECTORS_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://answers_checkpoints:${BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_MIGRATION_BASELINE_CONNECTION_URL="postgresql+psycopg://answers:${BACKEND_POSTGRES_USER_PASSWORD}@pgvector:5432/answers_baseline"
set -o history # turn it back on


source .venv/bin/activate

# alembic revision [-h] [-m MESSAGE] [--autogenerate] [--sql] [--head HEAD]
#    [--splice] [--branch-label BRANCH_LABEL] [--version-path VERSION_PATH]
#    [--rev-id REV_ID] [--depends-on DEPENDS_ON]

# See https://alembic.sqlalchemy.org/en/latest/autogenerate.html#auto-generating-migrations
# Also see https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#postgresql-schema-reflection

PYTHONPATH=./src alembic revision --autogenerate -m "$MESSAGE" 
