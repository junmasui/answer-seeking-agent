#!/usr/bin/env bash
# run-test.sh — Run a run-and-exit test service.
#
# Usage: run-test.sh <service>

set -euo pipefail

SERVICE="${1:?Usage: run-test.sh <service>}"

# ------------------------------------------------------------------
# Resolve compose working directory
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"
cd "$SERVICES_ROOT"

echo "[test] Running $SERVICE ..."
# Use --abort-on-container-exit to ensure the command exits when the container does.
# Use --exit-code-from to return the container's exit code.
# Use --attach to see output.
docker compose up --abort-on-container-exit --exit-code-from "$SERVICE" "$SERVICE"
