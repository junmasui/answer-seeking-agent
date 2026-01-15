#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

DOCKER="docker build"
# Use buildx if available for better caching and progress
if docker buildx version > /dev/null 2>&1; then
    DOCKER="docker buildx build"
fi

IMAGE_TAG="localhost/localhost/redis:7.4.1-custom"
LOG_DIR=../../../logs

mkdir -p $LOG_DIR

echo "Building ${IMAGE_TAG}..."

$DOCKER \
    --file Dockerfile \
    --build-context config-dir=../config \
    --tag "${IMAGE_TAG}" \
    --progress plain \
    --load \
    . 2>&1 \
| tee $LOG_DIR/build-redis.log

echo "Build complete: ${IMAGE_TAG}"
