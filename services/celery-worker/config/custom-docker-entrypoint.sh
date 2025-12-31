set -eu

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    # If running with NFS, we need to mask node_modules with a tmpfs so it's container-local
    echo "Running in NFS mode. Mounting file systems..."
    # The command must exactly match what is permitted in the /etc/sudoers file to avoid execution denial.
    sudo /usr/bin/mount /mnt/backend-nfs
    sudo /usr/bin/mount /app/backend

    # Ensure directory exists before mounting
    mkdir -p /app/backend/.venv
    # Check if already mounted (to avoid double mounting if container restarts but didn't fully die?) 
    # Actually, simpler to just try mount.
    sudo /usr/bin/mount /app/backend/.venv
fi

cd /app/backend

if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
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
    if [ "$GPU_MODE" == "cuda12" ]; then
        uv sync  --extra cuda12 --dev --all-packages
    elif [ "$GPU_MODE" == "cpu" ]; then
        uv sync  --extra cpu --dev --all-packages
    else
        echo "Unknown GPU_MODE: $GPU_MODE"
        exit -1
    fi
fi

source .venv/bin/activate

exec "$@"
