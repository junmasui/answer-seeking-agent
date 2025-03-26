
set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

set +o history # temporarily turn off history
SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
set -o history # turn it back on


if [ "$GPU_MODE" == "cuda12" ]; then
    nvidia-smi
fi

# NOTE: Run compile_requirements.sh after changes to dependencies
#
if [ "$GPU_MODE" == "cuda12" ]; then
    uv sync  --extra cuda12 --dev
elif [ "$GPU_MODE" == "cpu" ]; then
    uv sync  --extra cpu --dev
else
    exit -1
fi

# Run the FastAPI server.

set +o history # temporarily turn off history
export POSTGRES_ANSWERS_CONNECTION_URL="postgresql+psycopg://answers:${BACKEND_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_VECTORS_CONNECTION_URL="postgresql+psycopg://answers_vectors:${BACKEND_VECTORS_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://answers_checkpoints:${BACKEND_CHECKPOINTS_POSTGRES_USER_PASSWORD}@pgvector:5432/answers"
export POSTGRES_MIGRATION_BASELINE_CONNECTION_URL="postgresql+psycopg://answers:${BACKEND_POSTGRES_USER_PASSWORD}@pgvector:5432/answers_baseline"
set -o history # turn it back on

PYTHONPATH=./src \
uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- \
   uvicorn core_app:app --host 0.0.0.0 --port 8100
