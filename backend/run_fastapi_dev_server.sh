
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


PYTHONPATH=./src \
uv run --frozen --no-sync -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   -- python3 -m debugpy --listen 0.0.0.0:5678 -m uvicorn core_app:app --host 0.0.0.0 --port 8100
