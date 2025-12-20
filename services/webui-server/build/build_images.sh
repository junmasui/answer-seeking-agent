#!/usr/bin/env bash

## set -e: Exit immediately if a command exits with a non-zero status.
## set -u: Treat unset variables as an error and exit immediately.
set -eu


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

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config/ \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context frontend-dir=../../../frontend/ \
  --target production \
  --tag localhost/localhost/answers-frontend:node-22-bookworm \
  .

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config/ \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context frontend-dir=../../../frontend/ \
  --target dev \
  --tag localhost/localhost/answers-frontend-dev:node-22-bookworm \
  .
