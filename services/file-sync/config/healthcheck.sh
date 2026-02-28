#!/usr/bin/env bash
# Health check for dev-tools
# Dynamically verifies Mutagen sync sessions for running autotest containers

set -e

# If Mutagen sync is not enabled, we're healthy
if [ "${ENABLE_MUTAGEN_SYNC:-false}" != "true" ]; then
    exit 0
fi

# Check if mutagen binary exists
if ! command -v mutagen >/dev/null 2>&1; then
    echo "Mutagen not installed yet"
    exit 1
fi

# Discover which autotest containers are currently running
# Look for containers in our network that match autotest patterns
NETWORK="${COMPOSE_PROJECT_NAME:-agent-poc}"

# Get list of running containers in our network that match autotest/automated patterns
BACKEND_CONTAINERS=$(docker ps --filter "network=${NETWORK}" --format "{{.Names}}" 2>/dev/null | grep -E "(api-server-autotest|automated-pytest|celery-worker-autotest|celery-flower-autotest)" || echo "")
FRONTEND_CONTAINERS=$(docker ps --filter "network=${NETWORK}" --format "{{.Names}}" 2>/dev/null | grep -E "(webui-server-autotest|automated-vitest)" || echo "")

# Build list of expected session names based on running containers
EXPECTED_SESSIONS=""

for container in ${BACKEND_CONTAINERS}; do
    # Extract service name from container name (strip project prefix if present)
    # Container names are usually like "agent-automated-pytest-1" or "automated-pytest"
    service_name=$(echo "$container" | sed -E 's/^[^-]+-//' | sed 's/-[0-9]+$//' | sed 's/-run-[a-z0-9]+$//')
    EXPECTED_SESSIONS="${EXPECTED_SESSIONS} backend-${service_name}"
done

for container in ${FRONTEND_CONTAINERS}; do
    service_name=$(echo "$container" | sed -E 's/^[^-]+-//' | sed 's/-[0-9]+$//' | sed 's/-run-[a-z0-9]+$//')
    EXPECTED_SESSIONS="${EXPECTED_SESSIONS} frontend-${service_name}"
done

# If no autotest containers are running, we're healthy (nothing to sync)
if [ -z "$EXPECTED_SESSIONS" ]; then
    exit 0
fi

# Get current mutagen session list
MUTAGEN_OUTPUT=$(mutagen sync list 2>/dev/null || echo "")

if [ -z "$MUTAGEN_OUTPUT" ]; then
    echo "No Mutagen sessions exist yet, but have running containers"
    exit 1
fi

# Check each expected session
MISSING=0
UNHEALTHY=0

for session_name in ${EXPECTED_SESSIONS}; do
    # Check if this session exists
    if ! echo "$MUTAGEN_OUTPUT" | grep -q "Name: ${session_name}"; then
        echo "Missing session: ${session_name}"
        MISSING=$((MISSING + 1))
        continue
    fi
    
    # Extract the status for this specific session
    SESSION_BLOCK=$(echo "$MUTAGEN_OUTPUT" | awk "/Name: ${session_name}/,/^Name: /" | grep -v "^Name: " | head -20)
    
    # Check if session is in a healthy state (watching for changes)
    if echo "$SESSION_BLOCK" | grep -q "Status: Watching for changes"; then
        continue
    fi
    
    # Check for unhealthy states
    if echo "$SESSION_BLOCK" | grep -qE "Status: (Paused|Scanning|Staging|Connecting|Reconciling)"; then
        STATUS=$(echo "$SESSION_BLOCK" | grep "Status:" | head -1)
        echo "Session ${session_name} not ready: ${STATUS}"
        UNHEALTHY=$((UNHEALTHY + 1))
    else
        echo "Session ${session_name} in unknown state"
        UNHEALTHY=$((UNHEALTHY + 1))
    fi
done

if [ $MISSING -gt 0 ] || [ $UNHEALTHY -gt 0 ]; then
    echo "Health check failed: ${MISSING} missing, ${UNHEALTHY} not synchronized"
    exit 1
fi

# All expected sessions exist and are synchronized
exit 0
