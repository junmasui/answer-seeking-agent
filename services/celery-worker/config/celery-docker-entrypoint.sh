#!/bin/bash
set -eu

# Supervisor logic (if FUSE enabled)
if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
    echo "Running in FUSE mode with Supervisor..."
    mkdir -p /app/backend
    chown 1000:1000 /app/backend
    
    # Run Supervisor with the pre-baked configuration
    exec /usr/bin/supervisord -c /etc/supervisord.conf
else
    # Standard Mode (reuse existing logic if possible, or replicate it)
    # Since we can't easily reuse logic without calling scripts, allow me to replicate the standard non-FUSE flow.
    
    cd /app/backend

    if [ "${USE_FUSE_SRC_DIR:-false}" = "true" ]; then
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
        
        SYNC_CMD="uv sync --frozen --dev --all-packages"
        if [ "$GPU_MODE" == "cuda12" ]; then
            $SYNC_CMD --extra cuda12
        elif [ "$GPU_MODE" == "cpu" ]; then
            $SYNC_CMD --extra cpu
        else
            echo "Unknown GPU_MODE: $GPU_MODE"
            exit -1
        fi
    fi

    source .venv/bin/activate
    exec "$@"
fi
