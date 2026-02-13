#!/usr/bin/env bash

#
# Shared script to ensure the optimized BuildKit builder is healthy and active.
#
# Source this from build_images.sh scripts:
#   . "$(dirname "$0")/../../../scripts/ensure_buildx_builder.sh"
#
# After an OS or Docker upgrade the buildkit container backing the builder may
# become stale (runc shim mismatch).  We detect this by attempting to bootstrap
# the builder; if that fails we remove the broken instance and recreate it.
#

BUILDER_NAME="answers-optimized-builder"

_create_builder() {
    echo "Creating optimized builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" \
        --driver docker-container \
        --driver-opt default-load=true \
        --buildkitd-flags '--oci-worker-gc=true --oci-worker-gc-keepstorage=50000000000' \
        --bootstrap
}

if docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    # Builder exists — verify the backing container can actually start.
    if ! docker buildx inspect --bootstrap "$BUILDER_NAME" >/dev/null 2>&1; then
        echo "Builder $BUILDER_NAME exists but is unhealthy, recreating..."
        docker buildx rm "$BUILDER_NAME" 2>/dev/null || true
        _create_builder
    fi
else
    _create_builder
fi

docker buildx use "$BUILDER_NAME"
