#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build the customized Postgres image with the pgvector extension.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

# DOCKER=podman
DOCKER="docker buildx"
LOG_DIR=../../../../logs

mkdir -p $LOG_DIR

$DOCKER build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --tag localhost/localhost/postgres:17.2-with-pgvector \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-postgres.log
