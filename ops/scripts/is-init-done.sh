#!/usr/bin/env bash
# is-init-done.sh — Exit 0 if the init container already exited with code 0.
# Used by Taskfile `status:` checks to skip completed init containers.
#
# Usage: is-init-done.sh <service>

set -euo pipefail

SERVICE="${1:?Usage: is-init-done.sh <service>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"
cd "$SERVICES_ROOT"

json="$(docker compose ps --format json -a "$SERVICE" 2>/dev/null | head -1)" || true

if [[ -z "$json" || "$json" == "[]" ]]; then
    exit 1
fi

state="$(echo "$json" | jq -r '.State // ""')"
exit_code="$(echo "$json" | jq -r '.ExitCode // -1')"

if [[ "$state" == "exited" && "$exit_code" == "0" ]]; then
    exit 0
fi

exit 1
