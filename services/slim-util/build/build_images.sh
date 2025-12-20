#!/usr/bin/env bash

set -eu

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

$DOCKER build \
  --file Dockerfile \
  $DOCKER_BUILD_OPTS \
  --build-context parent-dir=.. \
  --tag localhost/localhost/debian-slim-util:1.0 \
  . 2>&1
