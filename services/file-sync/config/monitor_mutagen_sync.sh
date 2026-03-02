#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/mutagen-sync-monitor.lock"

echo "Starting mutagen sync monitor..."

while true; do
    # Short-circuit: skip if no autotest/automated-test containers are running
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qE '(autotest|automated-)'; then
        # Use flock to prevent overlapping runs
        (
            flock -n 9 || { echo "Sync already in progress, skipping"; exit 0; }
            bash /start_mutagen_sync.sh 2>&1 || true
        ) 9>"$LOCK_FILE"
    fi

    sleep 30
done
