
set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
set -o history # turn it back on

# Wait for dependency-gate to open.
#
source /wait_for_gate.sh

wait_for_dependency_gate /init-signal/backend-gate

if [ "$GPU_MODE" == "cuda12" ]; then
    nvidia-smi
fi

# NOTE: Run compile_requirements.sh after changes to dependencies
#
if [ "$GPU_MODE" == "cuda12" ]; then
    uv sync  --extra cuda12
elif [ "$GPU_MODE" == "cpu" ]; then
    uv sync  --extra cpu
else
    exit -1
fi

# Run the celery flower node.

set +o history # temporarily turn off history
export REDIS_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

export POSTGRES_ANSWERS_CONNECTION_URL="postgresql+psycopg://${ANSWERS_POSTGRES_USER_NAME}:${ANSWERS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_VECTORS_CONNECTION_URL="postgresql+psycopg://${VECTORS_POSTGRES_USER_NAME}:${VECTORS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://${CHECKPOINTS_POSTGRES_USER_NAME}:${CHECKPOINTS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"

export FLOWER_BASIC_AUTH=$CELERY_FLOWER_USER_NAME:$CELERY_FLOWER_USER_PASSWORD
set -o history # turn it back on

PYTHONPATH=./src \
uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- \
   celery --app=core_worker flower