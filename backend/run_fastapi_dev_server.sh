
nvidia-smi

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

PYTHONPATH=./src \
uv run --frozen --no-sync \
   -- \
   watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- \
   uvicorn core_app:app --host 0.0.0.0 --port 8100
