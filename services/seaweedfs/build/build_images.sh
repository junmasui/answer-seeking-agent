#!/bin/bash
set -e
set -o pipefail

# Change to the directory of this script
cd "$(dirname "$0")"

LOG_DIR=../../../logs
mkdir -p $LOG_DIR

#
# Setup optimized BuildKit builder with GC and health check
#
. "$(dirname "$0")/../../scripts/ensure_buildx_builder.sh"

# Build the image
docker buildx build \
    -f Dockerfile \
    -t localhost/localhost/seaweedfs:latest \
    --progress plain \
    . 2>&1 \
| tee $LOG_DIR/build-seaweedfs.log

docker buildx build \
    -f init.Dockerfile \
    --build-context config-dir=../config/ \
    -t localhost/localhost/init-seaweedfs:latest \
    --progress plain \
    . 2>&1 \
| tee $LOG_DIR/build-init-seaweedfs.log
