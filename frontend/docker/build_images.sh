#!/usr/bin/env bash

set -eu


#
# Build the frontend image.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

docker buildx build \
  --build-context parent-dir=.. \
  --tag localdomain-frontend:node-22-bookworm \
  .

#
# Build the customized Nginx image.
#
docker buildx build \
  --file nginx.Dockerfile \
  --tag localdomain-nginx:1.27-bookworm \
  .
