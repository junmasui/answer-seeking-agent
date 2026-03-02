#!/usr/bin/env bash
# compose-env.sh — Source this file to set COMPOSE_FILE and GPU_MODE.
# Usage: source "$(dirname "$0")/compose-env.sh"

set -euo pipefail

# Resolve the services/ directory relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SERVICES_ROOT="$(cd "$SCRIPT_DIR/../../services" && pwd)"

# GPU mode (default: cuda12)
export GPU_MODE="${GPU_MODE:-cuda12}"

# Build the COMPOSE_FILE list unless already provided
if [[ -z "${COMPOSE_FILE:-}" ]]; then
    if [[ "$GPU_MODE" == "cuda12" ]]; then
        export COMPOSE_FILE="common.compose.yml:cuda.compose.yml"
    else
        export COMPOSE_FILE="common.compose.yml:cpu-only.compose.yml"
    fi
fi

