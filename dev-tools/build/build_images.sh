#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build images for the dev-tools
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
LOG_DIR=../../logs
CACHE_DIR=../../.buildkit-cache

mkdir -p $LOG_DIR

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../services/scripts/ensure_buildx_builder.sh"

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Cache configuration for all builds
CACHE_OPTS="--cache-from type=local,src=$CACHE_DIR --cache-to type=local,dest=$CACHE_DIR,mode=min"

required_images=(
  "localhost/localhost/agent-frontend:node-22-bookworm"
  "localhost/localhost/agent-backend:python-3.12-cpu"
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
# Build a dev-tools image with Python 3.12 on Debian 12 (CPU only)
#
# NOTE: We use the default builder (host driver) because the optimized builder
# (docker-container driver) cannot access the locally built base images
# (node-source, backend-source) which are in the host daemon.
#

# Use default builder
docker buildx build --builder default \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config \
  --build-context node-source=docker-image://localhost/localhost/agent-frontend:node-22-bookworm \
  --build-context backend-source=docker-image://localhost/localhost/agent-backend:python-3.12-cpu \
  --target dev \
  --tag localhost/localhost/agent-dev-tools:python-3.12-cpu \
  --progress plain \
  --load \
  . 2>&1 \
| tee $LOG_DIR/build-dev-tools-python-cpu.log

#
# Build a dev-tools image with Python 3.12 on Debian 12 with CUDA 12
#

# Use default builder
docker buildx build --builder default \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file cuda13.Dockerfile \
  --build-context config-dir=../config \
  --build-context node-source=docker-image://localhost/localhost/agent-frontend:node-22-bookworm \
  --build-context backend-source=docker-image://localhost/localhost/agent-backend:python-3.12-cuda13 \
  --target dev \
  --tag localhost/localhost/agent-dev-tools:python-3.12-cuda13 \
  --progress plain \
  --load \
  . 2>&1 \
| tee $LOG_DIR/build-dev-tools-python-cuda13.log

# Cache GC is handled automatically by the BuildKit daemon
