#!/bin/bash
set -e

#
# This entrypoint script is responsible for setting up the environment
# for the dev-server container.
#

echo "Starting dev-server entrypoint..."

#
# Mount the NFS directory if requested
#
# Note: NFS and bind mounts are now handled by the root entrypoint

# If backend directory exists, then set up the Python environment.
if [ -d "/app/backend" ]; then
    (
        cd /app/backend

        if [ "${USE_CODEBASE_SYNC:-false}" = "true" ]; then

            echo "Waiting for synced backend source at /app/backend/pyproject.toml..."

            attempt=0
            while [ ! -f /app/backend/pyproject.toml ]; do
                sleep 1
                attempt=$((attempt+1))
                if [ $attempt -ge 30 ]; then
                    echo "Error: Backend source did not appear after 30 seconds."
                    exit 1
                fi
            done

            echo "Backend source detected."
        fi

        if [ "${USE_BOOTSTRAP_INSTALL:-false}" = "true" ]; then

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

        ls -la .

        if [ -f .venv/bin/activate ]; then
            # We source it here to verify it works, but sourcing in a subshell won't affect parent.
            # So we actually need to replicate the sourcing logic in the parent OR accept that 
            # the parent environment won't have the venv activated by default unless we do it again.
            # However, since the user asked if we should return to original directory, the implication 
            # is they MIGHT want to run commands elsewhere.
            # But normally we want 'exec "$@"' to run with the venv activated.
            true
        else
            echo "Warning: .venv/bin/activate not found."
        fi
    )
    
    # Re-activate in parent if available, but keep directory as original (likely /app)
    if [ -f "/app/backend/.venv/bin/activate" ]; then
        source /app/backend/.venv/bin/activate
    fi
else
    echo "Directory /app/backend not found. Skipping backend setup."
fi

# If frontend directory exists, then set up the ViteJS environment.
if [ -d "/app/frontend" ]; then
    (

        if [ "${USE_CODEBASE_SYNC:-false}" = "true" ]; then

            echo "Waiting for synced frontend source at /app/frontend/package.json..."

            attempt=0
            while [ ! -f /app/frontend/package.json ]; do
                sleep 1
                attempt=$((attempt+1))
                if [ $attempt -ge 30 ]; then
                    echo "Error: Frontend source did not appear after 30 seconds."
                    exit 1
                fi
            done

            echo "Frontend source detected."
        fi


        cd /app/frontend
        echo npm install
    )
else
    echo "Directory /app/frontend not found. Skipping frontend setup."
fi

exec "$@"
