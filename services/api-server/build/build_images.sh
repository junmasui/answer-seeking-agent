#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build a general image that is based on the official Python 3.12 on Debian 12 (Bookworm)
# with CUDA 12 and CUDNN 9 installed.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

# DOCKER=podman
DOCKER="docker buildx"
#DOCKER_BUILD_OPTS="--no-cache"
DOCKER_BUILD_OPTS=
LOG_DIR=../../../logs
CACHE_DIR=../../../.buildkit-cache

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../scripts/ensure_buildx_builder.sh"

# Create cache directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Cache configuration for all builds
CACHE_OPTS="--cache-from type=local,src=$CACHE_DIR --cache-to type=local,dest=$CACHE_DIR,mode=max"

echo "========================================"
echo "GROUP 1: Building base images in parallel"
echo "========================================"

#
# Build an image with Python 3.12 on Debian 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file Dockerfile \
    --target python3.12-cpu \
    --tag localhost/localhost/python:3.12.10-bookworm-cpu \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-python-bookworm-cpu.log
) &
PID_CPU_BASE=$!

#
# Build an image with CUDA12 installed on Python 3.12 on Debian 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file cuda12.Dockerfile \
    --target python3.12-cuda12-cudnn9 \
    --tag localhost/localhost/python:3.12.10-bookworm-cuda12-cudnn9 \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-python-bookworm-cuda12-cudnn9.log
) &
PID_CUDA_BASE=$!

# Wait for both base images to complete
echo "Waiting for base image builds to complete..."
wait $PID_CPU_BASE
wait $PID_CUDA_BASE
echo "✓ Base images completed"

echo ""
echo "========================================"
echo "GROUP 2: Building production backend images in parallel"
echo "========================================"

#
# Build a backend image with Python 3.12 on Debian 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file Dockerfile \
    --build-context config-dir=../config \
    --build-context celery-config-dir=../../celery-worker/config \
    --build-context dependency-gate-dir=../../dependency-gate \
    --build-context backend-dir=../../../backend \
    --target production \
    --tag localhost/localhost/answers-backend:python-3.12-cpu \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-backend-python-cpu.log
) &
PID_CPU_PROD=$!

#
# Build a backend image with Python 3.12 on Debian 12 with CUDA 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file cuda12.Dockerfile \
    --build-context config-dir=../config \
    --build-context celery-config-dir=../../celery-worker/config \
    --build-context dependency-gate-dir=../../dependency-gate \
    --build-context backend-dir=../../../backend \
    --target production \
    --tag localhost/localhost/answers-backend:python-3.12-cuda12 \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-backend-python-cuda12.log
) &
PID_CUDA_PROD=$!

# Wait for both production images to complete
echo "Waiting for production backend builds to complete..."
wait $PID_CPU_PROD
wait $PID_CUDA_PROD
echo "✓ Production backend images completed"

echo ""
echo "========================================"
echo "GROUP 3: Building dev backend images in parallel"
echo "========================================"

#
# Build a dev backend image with Python 3.12 on Debian 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file Dockerfile \
    --build-context config-dir=../config \
    --build-context celery-config-dir=../../celery-worker/config \
    --build-context dependency-gate-dir=../../dependency-gate \
    --build-context backend-dir=../../../backend \
    --target dev \
    --tag localhost/localhost/answers-backend-dev:python-3.12-cpu \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-backend-dev-python-cpu.log
) &
PID_CPU_DEV=$!

#
# Build a dev backend image with Python 3.12 on Debian 12 with CUDA 12
#
(
  $DOCKER build \
    $DOCKER_BUILD_OPTS \
    $CACHE_OPTS \
    --file cuda12.Dockerfile \
    --build-context config-dir=../config \
    --build-context celery-config-dir=../../celery-worker/config \
    --build-context dependency-gate-dir=../../dependency-gate \
    --build-context backend-dir=../../../backend \
    --target dev \
    --tag localhost/localhost/answers-backend-dev:python-3.12-cuda12 \
    --progress plain \
    . 2>&1 \
  | tee $LOG_DIR/build-backend-dev-python-cuda12.log
) &
PID_CUDA_DEV=$!

# Wait for both dev images to complete
echo "Waiting for dev backend builds to complete..."
wait $PID_CPU_DEV
wait $PID_CUDA_DEV
echo "✓ Dev backend images completed"

echo ""
echo "========================================"
echo "All builds completed successfully!"
echo "========================================"

#
# Clean up old cache (keep last 50GB)
#
echo ""
echo "Pruning old build cache..."
docker buildx prune --builder "$BUILDER_NAME" --keep-storage 50GB --force
