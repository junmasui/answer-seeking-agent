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
if [ "${USE_NFS_SRC_DIR:-false}" = "true" ]; then
    echo "Mounting NFS directory..."
    # Attempt to mount /mnt/data
    if mountpoint -q /mnt/data; then
        echo "/mnt/data is already mounted."
    else
        sudo mount /mnt/data || echo "Failed to mount /mnt/data, proceeding anyway (might be pre-mounted)."
    fi

    # Bind mount /mnt/data to /app
    echo "Bind mounting /mnt/data to /app..."
    sudo mount /app

    # Wait two seconds for the NFS server to start. This delay accounts for the periodic Unison
    # sync loop (Host -> /staging -> /exports) required to decouple the NFS export from the bind-mount.
    sleep 2

    # Bind mount .venv from /home/python/.venv-storage
    echo "Bind mounting .venv..."
    sudo mount /app/backend/.venv

    # Bind mount node_modules from /home/python/node_modules-storage
    # Note: user is python (uid 1000), but node stuff might be in frontend dir.
    # We mapped node_modules-storage to /app/frontend/node_modules in fstab/dockerfile.
    echo "Bind mounting node_modules..."
    sudo mount /app/frontend/node_modules
fi

# If backend directory exists, then set up the Python environment.
if [ -d "/app/backend" ]; then
    (
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
        cd /app/frontend
        echo npm install
    )
else
    echo "Directory /app/frontend not found. Skipping frontend setup."
fi

exec "$@"
