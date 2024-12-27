
set -eu

cd /app

uv venv /app/.local/venv

source /app/.local/venv/bin/activate
export UV_PROJECT_ENVIRONMENT=/app/.local/venv

exec $@
