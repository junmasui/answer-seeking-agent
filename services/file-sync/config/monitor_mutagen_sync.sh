#!/usr/bin/env bash
set -euo pipefail

# Continuously monitor for new autotest containers and create sync sessions

echo "Starting mutagen sync monitor..."

while true; do
    # Run sync creation script which will detect and create sessions for new containers
    if [ -f /start_mutagen_sync.sh ]; then
        bash /start_mutagen_sync.sh 2>&1 | grep -v "already exists" || true
    fi
    
    # Check every 5 seconds for new containers
    sleep 5
done
