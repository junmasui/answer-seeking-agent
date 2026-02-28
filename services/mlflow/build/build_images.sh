#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build MLFlow image with Postgres and S3 support
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
mkdir -p "$LOG_DIR"

# Cache configuration for all builds
CACHE_OPTS="--cache-from type=local,src=$CACHE_DIR --cache-to type=local,dest=$CACHE_DIR,mode=max"

#
# Build MLFlow image
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  $CACHE_OPTS \
  --file Dockerfile \
  --tag localhost/localhost/mlflow:latest \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-mlflow.log
