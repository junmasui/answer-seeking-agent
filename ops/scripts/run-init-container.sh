#!/usr/bin/env bash
# run-init-container.sh — Run a one-shot init container idempotently.
#
# Usage: run-init-container.sh <service>
#
# Behaviour:
#   1. If the container already exited with code 0 → skip.
#   2. If it exists in any other state → remove and re-run.
#   3. Start the container, wait for it to exit, verify exit code 0.

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
# Pre-check
# ------------------------------------------------------------------

read -r exists state exit_code <<< "$(get_state)"
echo "[init] pre-check $SERVICE: exists=$exists state=$state exit_code=$exit_code"

if [[ "$exists" == "true" && "$state" == "exited" && "$exit_code" == "0" ]]; then
    echo "[init] $SERVICE already completed successfully — skipping."
    exit 0
fi

if [[ "$exists" == "true" ]]; then
    echo "[init] Removing old container $SERVICE (state=$state exit=$exit_code)..."
    docker compose rm -f -s "$SERVICE" 2>/dev/null || true
fi

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------

echo "[init] Starting init container $SERVICE ..."
docker compose up -d "$SERVICE"

echo "[init] Waiting for $SERVICE to exit ..."
if docker compose wait "$SERVICE" 2>/dev/null; then
    echo "[init] $SERVICE completed successfully."
    exit 0
fi

# Fallback: docker compose wait can be flaky — inspect directly
container_id="$(docker compose ps -q -a "$SERVICE" 2>/dev/null)" || true
if [[ -n "$container_id" ]]; then
    actual_exit="$(docker inspect --format '{{.State.ExitCode}}' "$container_id" 2>/dev/null)" || true
    if [[ "$actual_exit" == "0" ]]; then
        echo "[init] WARNING: docker compose wait reported failure but container exited 0 — proceeding."
        exit 0
    fi
fi

echo "[init] ERROR: $SERVICE failed." >&2
docker compose logs --tail 50 "$SERVICE" >&2 || true
exit 1
