#!/bin/bash
set -e

# Change to the directory of this script
cd "$(dirname "$0")"

# Build the image
docker buildx build \
    -f Dockerfile \
    -t localhost/localhost/seaweedfs:latest .

docker buildx build \
    -f init.Dockerfile \
    --build-context config-dir=../config/ \
    -t localhost/localhost/init-seaweedfs:latest .
