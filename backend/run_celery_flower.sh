
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

# NOTE 1 regarding watchmdo:
#   There are two approaches to launching run-and-done executables from watchmedo:
#     * shell-command
#     * auto-restart with --no-restart-on-command-exit
#   The major difference between the two is: shell-command does not try to kill the prior
#   launchs, auto-restart does try to kill. For longer-running pytest commands, the prior
#   launch should be killed since it is only consuming resources for an obsolete set of changes.
#   Hence the auto-restart approach is choosen.
#
# NOTE 2 regarding watchmedo
#   A deep dive regarding pattern option in watchmedo:
#     You will need to start at
#     AutoRestartTrick (https://github.com/gorakhargosh/watchdog/blob/561aa0425c44b9d4376163f2b909bf1b655cf71a/src/watchdog/tricks/__init__.py#L147)
#     arriving at PatternMatchingEventHandler (https://github.com/gorakhargosh/watchdog/blob/561aa0425c44b9d4376163f2b909bf1b655cf71a/src/watchdog/events.py#L292)
#     then arriving at _match_path (https://github.com/gorakhargosh/watchdog/blob/561aa0425c44b9d4376163f2b909bf1b655cf71a/src/watchdog/utils/patterns.py#L24)
if [ -z "${WATCH_DEBOUNCE_SECS:-}" ]; then
    WATCH_DEBOUNCE_SECS=5.0
fi

PYTHONPATH=./src \
uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --debounce-interval=${WATCH_DEBOUNCE_SECS} \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- \
   celery --app=core_worker flower
