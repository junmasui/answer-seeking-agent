#!/bin/bash
set -eu

# NOTE: This script is overridden by /celery-docker-entrypoint.sh when built into the image for production/FUSE use.
# This file is kept if needed for local non-FUSE dev where it might be mounted, 
# although the compose file now points to the baked-in one in the image.

# If you are seeing this running, it means you are likely mounting this script over the image's one
# or running in a context where the image hasn't been updated.

# Reuse standard logic or legacy logic here if needed.
# For now, just a placeholder or fallback.

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
