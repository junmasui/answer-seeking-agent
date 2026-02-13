#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build the file-sync image
#
DOCKER="docker buildx"
LOG_DIR=../../../logs

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../scripts/ensure_buildx_builder.sh"

$DOCKER build \
  --file Dockerfile \
  --build-context config-dir=../config \
  --tag localhost/localhost/file-sync:latest \
  --progress plain \
  . 2>&1 \
| tee $LOG_DIR/build-file-sync.log
