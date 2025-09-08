#!/usr/bin/env bash

set -eu

#
# Build the customized Postgres image with the pgvector extension.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

# DOCKER=podman
DOCKER="docker buildx"

$DOCKER build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --tag localhost/localhost/postgres:17.2-with-pgvector \
  .
