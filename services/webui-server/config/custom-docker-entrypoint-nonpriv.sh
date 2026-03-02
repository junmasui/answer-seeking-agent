#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
for FILE in "${SECRETS_MOUNT}"/*_secrets
do
    [ -f "$FILE" ] || continue
    while IFS='=' read -r KEY VALUE || [ -n "$KEY" ]; do
      case "$KEY" in
        \#* | '') continue ;;
        *) export "$KEY=$VALUE" ;;
      esac
    done < "$FILE"
done


# Only run if codebase sync is enabled
if [ "${ENABLE_MUTAGEN_SYNC:-false}" = "true" ]; then

    MUTAGEN_SYNC_FILE="/app/frontend/.mutagen-sync-id"
    echo "Waiting for codebase sync... (looking for $MUTAGEN_SYNC_FILE)"

    # Block until the sentinel file appears.
    #
    # This mechanism relies on the fact that .mutagen-sync-id is NOT copied into
    # the Docker image during build (it is excluded via .dockerignore or simply not COPY'd).
    # Therefore, its presence in the container confirms that Mutagen has successfully
    # synced the source directory from the host.
    while [ ! -f "$MUTAGEN_SYNC_FILE" ]; do
        sleep 1
    done
    # For the static marker approach, we just verify the file exists and has content
    echo "Codebase sync verified: found $MUTAGEN_SYNC_FILE"

    echo "Waiting for synced frontend source at /app/frontend/package.json..."

    # Wait for key files to exist
    attempt=0
    while [ ! -f /app/frontend/package.json ] || [ ! -f /app/frontend/package-lock.json ]; do
        sleep 1
        attempt=$((attempt+1))
        if [ $attempt -ge 60 ]; then
            echo "Error: Frontend source did not appear after 60 seconds."
            exit 1
        fi
    done

    echo "Frontend source detected, verifying sync is complete..."
    
    # Wait for files to stabilize (no changes for 2 seconds)
    STABLE_COUNT=0
    LAST_MTIME=$(stat -c %Y /app/frontend/package.json 2>/dev/null || echo 0)
    
    while [ $STABLE_COUNT -lt 2 ]; do
        sleep 1
        CURRENT_MTIME=$(stat -c %Y /app/frontend/package.json 2>/dev/null || echo 0)
        
        if [ "$CURRENT_MTIME" = "$LAST_MTIME" ]; then
            STABLE_COUNT=$((STABLE_COUNT + 1))
        else
            STABLE_COUNT=0
            LAST_MTIME=$CURRENT_MTIME
        fi
        
        attempt=$((attempt+1))
        if [ $attempt -ge 90 ]; then
            echo "Warning: Files still changing after 90 seconds, proceeding anyway"
            break
        fi
    done

    # For automated test containers, also verify tests directory exists
    if [ "${APP_AUTORESTART:-true}" = "false" ]; then
        echo "Verifying tests directory is synced..."
        test_attempt=0
        while [ ! -d /app/frontend/tests ]; do
            sleep 1
            test_attempt=$((test_attempt+1))
            if [ $test_attempt -ge 30 ]; then
                echo "Error: tests/ directory did not appear after 30 seconds."
                echo "Contents of /app/frontend:"
                ls -la /app/frontend
                exit 1
            fi
        done
        echo "Tests directory detected."
    fi

    echo "Frontend source synchronized and stable."
fi

# Change directory. If we are mount file-systems, then this operation must
# wait until after the mounts are ready.
#
mkdir -p /app/frontend
cd /app/frontend

# Transition to the non-privileged entrypoint

exec "$@"
