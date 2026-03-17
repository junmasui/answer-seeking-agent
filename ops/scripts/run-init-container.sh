#!/usr/bin/env bash
# run-init-container.sh — Run a one-shot init container idempotently.
#
# Usage: run-init-container.sh <service>
#
# Behaviour:
#   1. If the container already exited with code 0 → skip.
#   2. Start the container in foreground, wait for it to exit.
#   3. Propagate the exit code.

set -euo pipefail

SERVICE="${1:?Usage: run-init-container.sh <service>}"

# ------------------------------------------------------------------
# Resolve compose working directory
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"
cd "$SERVICES_ROOT"

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

get_state() {
    local json
    json="$(docker compose ps --format json -a "$SERVICE" 2>/dev/null | head -1)" || true
    if [[ -z "$json" || "$json" == "[]" ]]; then
        echo "false '' -1"
        return
    fi
    local state exit_code
    state="$(echo "$json" | jq -r '.State // ""')"
    exit_code="$(echo "$json" | jq -r '.ExitCode // -1')"
    echo "true $state $exit_code"
}

# ------------------------------------------------------------------
# Pre-check (Idempotency)
# ------------------------------------------------------------------

read -r exists state exit_code <<< "$(get_state)"
echo "[init] pre-check $SERVICE: exists=$exists state=$state exit_code=$exit_code"

if [[ "$exists" == "true" && "$state" == "exited" && "$exit_code" == "0" ]]; then
    echo "[init] $SERVICE already completed successfully — skipping."
    exit 0
fi

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------

echo "[init] Starting init container $SERVICE ..."

# Use --force-recreate to ensure we don't just restart a failed container.
# Use --abort-on-container-exit to return to shell when done.
# Use --exit-code-from to propagate the container's status.
docker compose up \
    --force-recreate \
    --abort-on-container-exit \
    --exit-code-from "$SERVICE" \
    "$SERVICE"
