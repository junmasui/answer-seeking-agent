#!/usr/bin/env bash

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

$DOCKER build \
  --build-context parent-dir=.. \
  --tag localhost/localhost/answers-frontend:node-22-bookworm \
  .

