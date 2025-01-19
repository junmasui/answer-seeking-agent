
set -eu

cd /app

# Create the virtual environment only once.
#
# For the CACHEDIR.TAG specification, see https://bford.info/cachedir/
# For uv's explanation, see: https://github.com/astral-sh/uv/issues/1648
if [ ! -f "/app/.local/venv/CACHEDIR.TAG" ] \
    || ! ( grep -q "Signature: 8a477f597d28d172789f06886806bc55" "/app/.local/venv/CACHEDIR.TAG" )
then
    uv venv /app/.local/venv
fi

source /app/.local/venv/bin/activate
export UV_PROJECT_ENVIRONMENT=/app/.local/venv

exec $@
