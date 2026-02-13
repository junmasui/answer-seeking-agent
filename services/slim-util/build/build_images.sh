#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build a small Debian image with some utilities installed.
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

mkdir -p $LOG_DIR

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../scripts/ensure_buildx_builder.sh"

$DOCKER build \
  --file Dockerfile \
  $DOCKER_BUILD_OPTS \
  --build-context parent-dir=.. \
  --tag localhost/localhost/debian-slim-util:1.0 \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-slim-util.log
