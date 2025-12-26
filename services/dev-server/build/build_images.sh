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

mkdir -p $LOG_DIR

#
# Build a dev-server image with Python 3.12 on Debian 12 (CPU only)
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
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
  --file cuda12.Dockerfile \
  --build-context config-dir=../config \
  --target dev \
  --tag localhost/localhost/answers-dev-server:python-3.12-cuda12 \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-dev-server-python-cuda12.log
