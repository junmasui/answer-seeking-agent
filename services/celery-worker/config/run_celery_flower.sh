set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

if [ "$GPU_MODE" == "cuda13" ]; then
    nvidia-smi
fi

# NOTE: Run compile_requirements.sh after changes to dependencies
#
if [ "$GPU_MODE" == "cuda13" ]; then
    uv sync  --extra cuda13 --all-packages
elif [ "$GPU_MODE" == "cpu" ]; then
    uv sync  --extra cpu --all-packages
else
    exit -1
fi

# Run the celery flower node.

export REDIS_URL="redis://:${REDIS_DEFAULT_PASSWORD}@redis:6379/0"

export POSTGRES_AGENT_CONNECTION_URL="postgresql+psycopg://${AGENT_POSTGRES_USER_NAME}:${AGENT_POSTGRES_USER_PASSWORD}@postgres:5432/${AGENT_POSTGRES_DATABASE}"
export POSTGRES_CHECKPOINTS_CONNECTION_URL="postgresql+psycopg://${CHECKPOINTS_POSTGRES_USER_NAME}:${CHECKPOINTS_POSTGRES_USER_PASSWORD}@postgres:5432/${AGENT_POSTGRES_DATABASE}"

export FLOWER_BASIC_AUTH="$CELERY_FLOWER_USER_NAME:$CELERY_FLOWER_USER_PASSWORD"

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

# Signal readiness for the two-phase Docker health check.
# At this point the Python environment is fully synced.
touch "${HEALTHCHECK_READY_FILE:-/tmp/app-ready}"

uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --debug-force-polling \
   --debounce-interval="${WATCH_DEBOUNCE_SECS}" \
   --directory=./apps --directory=./libs  --recursive --pattern='*.py' \
   -- \
   celery --app=core_worker flower
