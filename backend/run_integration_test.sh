
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

wait_for_dependency_gate /init-signal/backend-test-gate

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

# Run the integration tests.

set +o history # temporarily turn off history
export REDIS_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

export POSTGRES_ANSWERS_CONNECTION_URL="postgresql+psycopg://${ANSWERS_POSTGRES_USER_NAME}:${ANSWERS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_VECTORS_CONNECTION_URL="postgresql+psycopg://${VECTORS_POSTGRES_USER_NAME}:${VECTORS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://${CHECKPOINTS_POSTGRES_USER_NAME}:${CHECKPOINTS_POSTGRES_USER_PASSWORD}@pgvector:5432/${ANSWERS_POSTGRES_DATABASE}"
set -o history # turn it back on

# watchmedo 
# fs.inotify.max_user_instances = 512
# fs.inotify.max_user_watches = 524288
#

# There are two approaches to launching run-and-done executables
# from watchmedo:
#  * shell-command
#  * auto-restart with --no-restart-on-command-exit
# The first approach is better suited for quick commands. shell-command does
# not attempt to kill the prior launchs. For longer-running pytest commands,
# the prior launch should be killed since it is only consuming resources
# for an obsolete trigger. Hence the second approach is choosen.
#
PYTHONPATH=./src:./tests \
uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --no-restart-on-command-exit \
   --debounce-interval=5.0 \
   --directory=./src --directory=./tests  --recursive --pattern='*.py' \
   -- \
   pytest -v -v --capture=tee-sys tests

