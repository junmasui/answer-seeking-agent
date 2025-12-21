set -eu

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    # The command must exactly match what is permitted in the /etc/sudoers file to avoid execution denial.
    sudo /usr/bin/mount /app/backend
fi

cd /app/backend

# If running with NFS, we need to mask .venv with a bind mount so it's container-local
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Running in NFS mode. Mounting internal storage on .venv..."
    # Ensure directory exists before mounting
    mkdir -p /app/backend/.venv
    
    # Bind mount the container-local storage to the NFS path
    sudo /usr/bin/mount /app/backend/.venv

    # Create the virtual environment only once.
    #
    # For the CACHEDIR.TAG specification, see https://bford.info/cachedir/
    # For uv's explanation, see: https://github.com/astral-sh/uv/issues/1648
    if [ ! -f ".venv/CACHEDIR.TAG" ] \
        || ! ( grep -q "Signature: 8a477f597d28d172789f06886806bc55" ".venv/CACHEDIR.TAG" )
    then
        uv venv --allow-existing
    fi

    # Sync the virtual environment (persistent across restarts now)
    uv sync --extra cpu --dev --all-packages
fi

ls -la .

source .venv/bin/activate

exec "$@"
