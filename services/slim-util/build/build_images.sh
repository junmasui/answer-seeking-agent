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

$DOCKER build \
  --file Dockerfile \
  --no-cache \
  --build-context parent-dir=.. \
  --tag localhost/localhost/debian-slim-util:1.0 \
  . 2>&1
