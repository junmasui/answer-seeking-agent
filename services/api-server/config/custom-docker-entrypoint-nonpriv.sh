#!/usr/bin/env bash
set -eu

# Note: NFS and venv mounts are now handled by the root entrypoint

cd /app/backend

if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then

    # Wait for mount
    attempt=0
    while ! mountpoint -q /app/backend; do
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 30 ]; then
            echo "Error: Mount failed to appear after 30 seconds."
            exit 1
        fi
    done

    echo "Mount active."

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

source .venv/bin/activate

exec "$@"
