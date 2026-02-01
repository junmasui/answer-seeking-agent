#!/usr/bin/env bash
set -eu

# Note: NFS and venv mounts are now handled by the root entrypoint

mkdir -p /app/backend
cd /app/backend

if [ "${USE_CODEBASE_SYNC:-false}" = "true" ]; then

    echo "Waiting for synced backend source at /app/backend/pyproject.toml..."
    
    # Wait for key files to exist
    attempt=0
    while [ ! -f /app/backend/pyproject.toml ] || [ ! -f /app/backend/uv.lock ]; do
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 60 ]; then
            echo "Error: Backend source did not appear after 60 seconds."
            exit 1
        fi
    done

    echo "Backend source detected, verifying sync is complete..."
    
    # Wait for files to stabilize (no changes for 2 seconds)
    # This ensures we're not mid-sync
    STABLE_COUNT=0
    LAST_MTIME=$(stat -c %Y /app/backend/pyproject.toml 2>/dev/null || echo 0)
    
    while [ $STABLE_COUNT -lt 2 ]; do
        sleep 1
        CURRENT_MTIME=$(stat -c %Y /app/backend/pyproject.toml 2>/dev/null || echo 0)
        
        if [ "$CURRENT_MTIME" = "$LAST_MTIME" ]; then
            STABLE_COUNT=$((STABLE_COUNT + 1))
        else
            STABLE_COUNT=0
            LAST_MTIME=$CURRENT_MTIME
        fi
        
        attempt=$((attempt+1))
        if [ $attempt -ge 90 ]; then
            echo "Warning: Files still changing after 90 seconds, proceeding anyway"
            break
        fi
    done

    echo "Backend source synchronized and stable."
fi

# Change directory. If we are mount file-systems, then this operation must
# wait until after the mounts are ready.
#
cd /app/backend


if [ "${USE_BOOTSTRAP_INSTALL:-false}" = "true" ]; then

    # Create or ensure the virtual environment exists.
    uv venv --allow-existing

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

# Wait for valid virtual environment
attempt=0
while [ ! -f ".venv/bin/activate" ]; do
    echo "Waiting for .venv/bin/activate..."
    sleep 1
    attempt=$((attempt+1))
    if [ $attempt -ge 10 ]; then
         echo "Error: .venv/bin/activate not found after 10 seconds."
         ls -la .venv || true
         exit 1
    fi
done

source .venv/bin/activate

exec "$@"
