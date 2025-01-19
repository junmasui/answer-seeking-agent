
nvidia-smi



# uv pip compile -o requirements.compiled.txt pyproject.toml
uv pip sync -r requirements.compiled.txt

uv run --frozen -- watchmedo auto-restart \
   --directory=.  --recursive --pattern='*.py;*.env' \
   --ignore-pattern='./logging.toml' \
   -- celery --app=worker worker -l INFO
