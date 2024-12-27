
nvidia-smi



# uv pip compile -o requirements.compiled.txt pyproject.toml
uv pip install -r requirements.compiled.txt

# uv run --frozen -- celery --app=worker worker -l INFO
uv run --frozen -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env;*.json;*.toml' \
   -- celery --app=worker worker -l DEBUG
