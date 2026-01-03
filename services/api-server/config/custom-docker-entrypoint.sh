set -eu

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    # If running with NFS, we need to mask node_modules with a tmpfs so it's container-local
    echo "Running in NFS mode. Mounting file systems..."
    # The command must exactly match what is permitted in the /etc/sudoers file to avoid execution denial.
    sudo /usr/bin/mount /mnt/backend-nfs
    sudo /usr/bin/mount /app/backend

    # Wait two seconds for the NFS server to start. This delay accounts for the periodic Unison
    # sync loop (Host -> /staging -> /exports) required to decouple the NFS export from the bind-mount.
    sleep 2

    # Ensure directory exists before mounting
    mkdir -p /app/backend/.venv
    # Check if already mounted (to avoid double mounting if container restarts but didn't fully die?) 
    # Actually, simpler to just try mount.
    sudo /usr/bin/mount /app/backend/.venv
fi

if [ "${USE_LOCAL_VENV_DIR:-false}" = "true" ]; then
    # Ensure directory exists before mounting
    #mkdir -p /app/backend/.venv
    # Check if already mounted (to avoid double mounting if container restarts but didn't fully die?) 
    # Actually, simpler to just try mount.
    sudo /usr/bin/mount /app/backend/.venv
fi

cd /app/backend

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ] || [ "${USE_LOCAL_VENV_DIR:-false}" = "true" ]; then
    #    
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
    # Use --frozen to prevent writing to the lockfile (which might be read-only or owned by another user)
    SYNC_CMD="uv sync --frozen --dev --all-packages"

    SYNC_CMD="uv sync --frozen --dev --all-packages"
    EXTRA_ARGS=""

    if [ "$GPU_MODE" == "cuda12" ]; then
        EXTRA_ARGS="--extra cuda12"
    elif [ "$GPU_MODE" == "cpu" ]; then
        EXTRA_ARGS="--extra cpu"
    else
        echo "Unknown GPU_MODE: $GPU_MODE"
        exit -1
    fi

    set +e
    # shellcheck disable=SC2086
    $SYNC_CMD $EXTRA_ARGS
    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -ne 0 ]; then
        echo "Error: Failed to sync virtual environment."
        echo "This is likely because uv.lock is not up-to-date with pyproject.toml."
        echo "Please run 'uv lock' on your host machine to update uv.lock."
        exit $EXIT_CODE
    fi
fi

ls -la .

source .venv/bin/activate

exec "$@"
