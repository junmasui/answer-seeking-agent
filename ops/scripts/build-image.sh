#!/usr/bin/env bash
# build-image.sh — Build a custom Docker image for a service.
#
# Usage: build-image.sh <service-dir>
#
# Expects: services/<service-dir>/build/build_images.sh

set -euo pipefail

DIR="${1:?Usage: build-image.sh <service-dir>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"

BUILD_DIR="$SERVICES_ROOT/$DIR/build"
BUILD_SCRIPT="$BUILD_DIR/build_images.sh"

if [[ ! -f "$BUILD_SCRIPT" ]]; then
    echo "ERROR: Missing build script: $BUILD_SCRIPT" >&2
    exit 1
fi

echo "[build-image] Building $DIR ..."
cd "$BUILD_DIR"
bash build_images.sh
echo "[build-image] $DIR built successfully."
