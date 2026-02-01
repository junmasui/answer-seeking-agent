#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build images for the dev-server
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

cd "$(dirname "$0")"

# DOCKER=podman
DOCKER="docker buildx"
#DOCKER_BUILD_OPTS="--no-cache"
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

required_images=(
  "localhost/localhost/answers-frontend:node-22-bookworm"
  "localhost/localhost/answers-backend:python-3.12-cpu"
)

missing_images=()
for image in "${required_images[@]}"; do
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    missing_images+=("$image")
  fi
done

if [ ${#missing_images[@]} -gt 0 ]; then
  echo "Missing required base images:" >&2
  for image in "${missing_images[@]}"; do
    echo "  - $image" >&2
  done
  echo "Build them first with:" >&2
  echo "  /home/jun/research/answer-seeking-agent/services/webui-server/build/build_images.sh" >&2
  echo "  /home/jun/research/answer-seeking-agent/services/api-server/build/build_images.sh" >&2
  exit 1
fi

#
# Build a dev-server image with Python 3.12 on Debian 12 (CPU only)
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config \
  --target dev \
  --tag localhost/localhost/answers-dev-server:python-3.12-cpu \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-dev-server-python-cpu.log

#
# Build a dev-server image with Python 3.12 on Debian 12 with CUDA 12
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file cuda12.Dockerfile \
  --build-context config-dir=../config \
  --target dev \
  --tag localhost/localhost/answers-dev-server:python-3.12-cuda12 \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-dev-server-python-cuda12.log

#
# Clean up old cache (keep last 50GB)
#
echo "Pruning old build cache..."
docker buildx prune --builder "$BUILDER_NAME" --keep-storage 50GB --force
