#!/usr/bin/env bash
# stop-services.sh — Stop and remove a list of Docker Compose services.
#
# Usage: stop-services.sh <service1> [service2] ...
#        stop-services.sh --all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/compose-env.sh"
cd "$SERVICES_ROOT"

if [[ "${1:-}" == "--all" ]]; then
    echo "[stop] Stopping all services and removing orphans ..."
    docker compose --profile all down --remove-orphans
    echo "[stop] All services stopped."
    exit 0
fi

if [[ $# -eq 0 ]]; then
    echo "Usage: stop-services.sh <service1> [service2] ... | --all" >&2
    exit 1
fi

echo "[stop] Stopping: $* ..."
docker compose stop "$@"
docker compose rm -f "$@"
echo "[stop] Services stopped and removed."
