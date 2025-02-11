#!/usr/bin/env bash

set -eu

#
# Build the customized Langfuse images.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#
docker buildx build \
  --build-context parent-dir=.. \
  --file langfuse.Dockerfile \
  --tag localhost/langfuse:3.24-plus-extras \
  .

docker buildx build \
  --build-context parent-dir=.. \
  --file langfuse-worker.Dockerfile \
  --tag localhost/langfuse-worker:3.24-plus-extras \
  .
