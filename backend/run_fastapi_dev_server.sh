
nvidia-smi


# uv pip compile pyproject.toml --all-extras -o requirements.compiled.txt
uv pip sync -r requirements.compiled.txt

uv run --frozen -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   --ignore-pattern='./logging.toml' \
   -- uvicorn demo-app:app --host 0.0.0.0 --port 8100
