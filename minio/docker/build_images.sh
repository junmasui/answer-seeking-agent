#!/usr/bin/env bash

set -eu

#
# Build the customized Minio image.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#
docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --tag localdomain-minio:2024-12-13T22-19-12Z \
  .
