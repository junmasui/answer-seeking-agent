#!/usr/bin/env bash
# is-service-running.sh — Exit 0 if the service is running and healthy, 1 otherwise.
# Used by Taskfile `status:` checks to skip already-running services.
#
# Usage: is-service-running.sh <service>

set -euo pipefail

SERVICE="${1:?Usage: is-service-running.sh <service>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"
cd "$SERVICES_ROOT"

json="$(docker compose ps --format json -a "$SERVICE" 2>/dev/null | head -1)" || true

if [[ -z "$json" || "$json" == "[]" ]]; then
    exit 1
fi

state="$(echo "$json" | jq -r '.State // ""')"
health="$(echo "$json" | jq -r '.Health // ""')"

if [[ "$state" == "running" && ( "$health" == "" || "$health" == "healthy" ) ]]; then
    exit 0
fi

exit 1
