#!/usr/bin/env bash
set -eu

# Note: NFS and venv mounts are now handled by the root entrypoint

mkdir -p /app/backend
cd /app/backend

if [ "${ENABLE_MUTAGEN_SYNC:-false}" = "true" ]; then

    MUTAGEN_SYNC_FILE="/app/backend/.mutagen-sync-id"

    echo "Waiting for codebase sync... (looking for $MUTAGEN_SYNC_FILE)"

    # Block until the sentinel file appears.
    #
    # This mechanism relies on the fact that .mutagen-sync-id is NOT copied into
    # the Docker image during build (it is excluded via .dockerignore or simply not COPY'd).
    # Therefore, its presence in the container confirms that Mutagen has successfully
    # synced the source directory from the host.
    while [ ! -f "$MUTAGEN_SYNC_FILE" ]; do
        sleep 1
    done
    # For the static marker approach, we just verify the file exists and has content
    echo "Codebase sync verified: found $MUTAGEN_SYNC_FILE"

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

    echo "Creating virtual environment exists."

    ls -al .
    ls -al .venv || true

    # Create or ensure the virtual environment exists.
    uv venv --allow-existing

    # PHASE 1: Sync all packages as non-editable (production-like)
    # This ensures all packages including telemetry are properly installed with entrypoints
    SYNC_CMD="uv sync --frozen --dev --all-packages"

    EXTRA_ARGS=""

    if [ "$GPU_MODE" == "cuda13" ]; then
        EXTRA_ARGS="--extra cuda13"
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

    if [ $EXIT_CODE -ne 0 ]; then
        echo "Error: Failed to sync virtual environment."
        echo "This is likely because uv.lock is not up-to-date with pyproject.toml."
        echo "Please run 'uv lock' on your host machine to update uv.lock."
        exit $EXIT_CODE
    fi

    set -e
fi

# Wait for valid virtual environment.
# Skip when the container's own command is responsible for creating the venv
# (e.g. python-build), to avoid a deadlock where the entrypoint waits for a
# venv that only the command itself would produce.
if [ "${USE_BOOTSTRAP_INSTALL:-false}" != "true" ]; then
    attempt=0
    while [ ! -f ".venv/bin/activate" ]; do
        echo "Waiting for .venv/bin/activate..."
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 30 ]; then
             echo "Error: .venv/bin/activate not found after 30 seconds."
             ls -la .venv || true
             exit 1
        fi
    done
fi

source .venv/bin/activate

exec "$@"
