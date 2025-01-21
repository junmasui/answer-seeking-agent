
set -eu

cd /app

ls -la .
ls -la .venv
ls -la /home
ls -la /home/python

# Create the virtual environment only once.
#
# For the CACHEDIR.TAG specification, see https://bford.info/cachedir/
# For uv's explanation, see: https://github.com/astral-sh/uv/issues/1648
if [ ! -f ".venv/CACHEDIR.TAG" ] \
    || ! ( grep -q "Signature: 8a477f597d28d172789f06886806bc55" ".venv/CACHEDIR.TAG" )
then
    uv venv
fi

source .venv/bin/activate

exec $@
