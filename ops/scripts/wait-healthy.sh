#!/usr/bin/env bash
# wait-healthy.sh — Start a long-running service and wait until it is healthy.
#
# Usage: wait-healthy.sh <service> [timeout_seconds]
#
# Behaviour:
#   1. Query the current container state.
#   2. If already running and healthy → exit 0 (skip).
#   3. If in a bad state (unhealthy / exited non-zero / dead) → force-remove, then start.
#   4. Otherwise → start.
#   5. Poll until healthy or timeout.

set -euo pipefail

SERVICE="${1:?Usage: wait-healthy.sh <service> [timeout]}"
TIMEOUT="${2:-120}"
POLL_INTERVAL=4

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
    # Returns: exists state health exit_code
    local json
    json="$(docker compose ps --format json -a "$SERVICE" 2>/dev/null | head -1)" || true
    if [[ -z "$json" || "$json" == "[]" ]]; then
        echo "false|||-1"
        return
    fi
    local state health exit_code
    state="$(echo "$json" | jq -r '.State // ""')"
    health="$(echo "$json" | jq -r '.Health // ""')"
    exit_code="$(echo "$json" | jq -r '.ExitCode // -1')"
    echo "true|$state|$health|$exit_code"
}

is_running_ok() {
    local exists="$1" state="$2" health="$3"
    [[ "$exists" == "true" && "$state" == "running" && ( "$health" == "" || "$health" == "healthy" ) ]]
}

force_remove() {
    echo "[wait-healthy] Removing $SERVICE (bad state)..."
    docker compose rm -f -s "$SERVICE" 2>/dev/null || true
}

# ------------------------------------------------------------------
# Pre-check
# ------------------------------------------------------------------

IFS='|' read -r exists state health exit_code <<< "$(get_state)"
echo "[wait-healthy] pre-check $SERVICE: exists=$exists state=$state health=$health exit_code=$exit_code"

if is_running_ok "$exists" "$state" "$health"; then
    echo "[wait-healthy] $SERVICE already running and healthy — skipping."
    exit 0
fi

if [[ "$exists" == "true" ]]; then
    if [[ "$health" == "unhealthy" \
       || ( "$state" == "exited" && "$exit_code" != "0" ) \
       || "$state" == "dead" || "$state" == "paused" || "$state" == "restarting" ]]; then
        force_remove
    fi
fi

# ------------------------------------------------------------------
# Start
# ------------------------------------------------------------------

echo "[wait-healthy] Starting $SERVICE ..."
docker compose up -d "$SERVICE"

# ------------------------------------------------------------------
# Poll for healthy
# ------------------------------------------------------------------

deadline=$((SECONDS + TIMEOUT))
while true; do
    IFS='|' read -r exists state health exit_code <<< "$(get_state)"
    echo "[wait-healthy] poll $SERVICE: state=$state health=$health"

    if is_running_ok "$exists" "$state" "$health"; then
        echo "[wait-healthy] $SERVICE is running and healthy."
        exit 0
    fi

    if [[ "$state" == "running" && "$health" == "starting" ]]; then
        if (( SECONDS < deadline )); then
            sleep "$POLL_INTERVAL"
            continue
        fi
        echo "[wait-healthy] ERROR: $SERVICE health-check did not pass within ${TIMEOUT}s" >&2
        exit 1
    fi

    echo "[wait-healthy] ERROR: $SERVICE not ready (state=$state health=$health)" >&2
    docker compose logs --tail 50 "$SERVICE" >&2 || true
    exit 1
done
