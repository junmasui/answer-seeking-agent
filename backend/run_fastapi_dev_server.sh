
nvidia-smi

# NOTE: Run compile_requirements.sh after changes to dependencies
#
if [ "$GPU_MODE" == "cuda12" ]; then
    uv pip sync --index-strategy=unsafe-best-match requirements-cuda12.compiled.txt
elif [ "$GPU_MODE" == "cpu" ]; then
    uv pip sync --index-strategy=unsafe-best-match requirements.compiled.txt
else
    exit -1
fi

uv run --frozen --no-sync -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- uvicorn demo-app:app --host 0.0.0.0 --port 8100
