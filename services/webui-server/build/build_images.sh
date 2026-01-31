#!/usr/bin/env bash

## set -e: Exit immediately if a command exits with a non-zero status.
## set -u: Treat unset variables as an error and exit immediately.
set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.


#
# Build the frontend image.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

# DOCKER=podman
DOCKER="docker buildx"
# DOCKER_BUILD_OPTS="--no-cache"
DOCKER_BUILD_OPTS=
LOG_DIR=../../../logs
CACHE_DIR=../../../.buildkit-cache

mkdir -p $LOG_DIR

#
# Setup optimized BuildKit builder with GC
#
BUILDER_NAME="answers-optimized-builder"
if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
    echo "Creating optimized builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" \
        --driver docker-container \
        --driver-opt default-load=true \
        --buildkitd-flags '--oci-worker-gc=true --oci-worker-gc-keepstorage=50000000000' \
        --bootstrap
fi

# Use the optimized builder
docker buildx use "$BUILDER_NAME"

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Cache configuration for all builds
CACHE_OPTS="--cache-from type=local,src=$CACHE_DIR --cache-to type=local,dest=$CACHE_DIR,mode=max"

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config/ \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context frontend-dir=../../../frontend/ \
  --target production \
  --tag localhost/localhost/answers-frontend:node-22-bookworm \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-frontend.log

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config/ \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context frontend-dir=../../../frontend/ \
  --target dev \
  --tag localhost/localhost/answers-frontend-dev:node-22-bookworm \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-frontend-dev.log

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config/ \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context frontend-dir=../../../frontend/ \
  --target test-xvfb \
  --tag localhost/localhost/answers-frontend-test-xvfb:node-22-bookworm \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-frontend-test-xvfb.log

#
# Clean up old cache (keep last 50GB)
#
echo "Pruning old build cache..."
docker buildx prune --builder "$BUILDER_NAME" --keep-storage 50GB --force
