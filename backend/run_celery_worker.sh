
nvidia-smi

# NOTE: Run compile_requirements.sh after changes to dependencies
#
if [ "$GPU_MODE" == "cuda12" ]; then
    uv pip sync --index-strategy=unsafe-best-match requirements-cuda12.compiled.txt
elif [ "$GPU_MODE" == "cpu" ]; then
    uv pip sync --index-strategy=unsafe-best-match requirements-cpu.compiled.txt
else
    exit -1
fi

PYTHON_CMD_OPTIONS="-m celery --app=core_worker worker -l INFO"

PYTHON_CMD_OPTIONS="-m debugpy --listen 0.0.0.0:5678 ${PYTHON_CMD_OPTIONS}"

# Run the celery worker with debugpy.
PYTHON_CMD="python3 ${PYTHON_CMD_OPTIONS}"

# Use watchmedo to restart on file changes.
WATCHMEDO_OPTIONS="auto-restart --directory=.  --recursive --pattern='*.py;*.env'"
PYTHON_CMD="watchmedo ${WATCHMEDO_OPTIONS} -- ${PYTHON_CMD}"

echo "${PYTHON_CMD}"

# Use 'uv run' to run the celery worker.
PYTHONPATH=./src \
    uv run --frozen --no-sync -- ${PYTHON_CMD}
