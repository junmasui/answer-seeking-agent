
nvidia-smi


# uv pip compile -o requirements.compiled.txt pyproject.toml
uv pip install -r requirements.compiled.txt

uv run --frozen -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env;*.json;*.toml' \
   -- uvicorn demo-app:app --host 0.0.0.0 --port 8100
