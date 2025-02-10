
set -eu

cd /app

# Create the virtual environment only once.
#
# For the CACHEDIR.TAG specification, see https://bford.info/cachedir/
# For uv's explanation, see: https://github.com/astral-sh/uv/issues/1648
if [ ! -f ".venv/CACHEDIR.TAG" ] \
    || ! ( grep -q "Signature: 8a477f597d28d172789f06886806bc55" ".venv/CACHEDIR.TAG" )
then
    # We want to create the virtual env even in the presence of
    # a hidden tag file.
    uv venv --allow-existing
fi

source .venv/bin/activate

exec $@
