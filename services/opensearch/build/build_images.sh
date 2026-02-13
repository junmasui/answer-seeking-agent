#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

DOCKER="docker buildx build"
IMAGE_TAG="localhost/localhost/opensearch:2.17.1-custom"
LOG_DIR=../../../logs

mkdir -p $LOG_DIR

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../scripts/ensure_buildx_builder.sh"

echo "Building ${IMAGE_TAG}..."

$DOCKER \
    --file Dockerfile \
    --build-context config-dir=../config \
    --tag "${IMAGE_TAG}" \
    --progress plain \
    --load \
    . 2>&1 \
| tee $LOG_DIR/build-opensearch.log

echo "Build complete: ${IMAGE_TAG}"
