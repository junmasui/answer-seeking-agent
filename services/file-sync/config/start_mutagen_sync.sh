#!/usr/bin/env bash
set -euo pipefail

MUTAGEN_SOURCE_ROOT="${MUTAGEN_SOURCE_ROOT:-/app}"
MUTAGEN_SSH_USER="${MUTAGEN_SSH_USER:-root}"
MUTAGEN_SSH_PORT="${MUTAGEN_SSH_PORT:-22}"
MUTAGEN_SSH_KEY_PATH="${MUTAGEN_SSH_KEY_PATH:-/run/secrets/mutagen_ssh_private_key}"
MUTAGEN_SYNC_MODE="${MUTAGEN_SYNC_MODE:-one-way-replica}"
# Detect the actual network name - it may have project prefix
NETWORK=$(docker network ls --format "{{.Name}}" | grep -E "agent-poc$" | head -1)

# Discover running autotest containers dynamically
echo "Discovering running autotest containers..."
BACKEND_CONTAINERS=$(docker ps --filter "network=${NETWORK}" --format "{{.Names}}" 2>/dev/null | grep -E "(api-server-autotest|automated-pytest|celery-worker-autotest|celery-flower-autotest)" || echo "")
FRONTEND_CONTAINERS=$(docker ps --filter "network=${NETWORK}" --format "{{.Names}}" 2>/dev/null | grep -E "(webui-server-autotest|automated-vitest)" || echo "")

# Extract service names from container names
# Handle both regular containers (agent-service-1) and run containers (agent-service-run-hash)
BACKEND_TARGETS=""
for container in ${BACKEND_CONTAINERS}; do
    # Strip project prefix, -run- suffix with hash, and trailing numbers
    service_name=$(echo "$container" | sed -E 's/^[^-]+-//' | sed -E 's/-run-[a-z0-9]+$//' | sed -E 's/-[0-9]+$//')
    BACKEND_TARGETS="${BACKEND_TARGETS} ${service_name}"
done

FRONTEND_TARGETS=""
for container in ${FRONTEND_CONTAINERS}; do
    # Strip project prefix, -run- suffix with hash, and trailing numbers
    service_name=$(echo "$container" | sed -E 's/^[^-]+-//' | sed -E 's/-run-[a-z0-9]+$//' | sed -E 's/-[0-9]+$//')
    FRONTEND_TARGETS="${FRONTEND_TARGETS} ${service_name}"
done

echo "Backend targets: ${BACKEND_TARGETS:-none}"
echo "Frontend targets: ${FRONTEND_TARGETS:-none}"

if [ -z "$BACKEND_TARGETS" ] && [ -z "$FRONTEND_TARGETS" ]; then
    echo "No autotest containers running, skipping Mutagen sync setup"
    exit 0
fi

if [ -f "$MUTAGEN_SSH_KEY_PATH" ]; then
    mkdir -p /root/.ssh
    chmod 700 /root/.ssh
    cp "$MUTAGEN_SSH_KEY_PATH" /root/.ssh/mutagen_id
    chmod 600 /root/.ssh/mutagen_id
    cat <<EOF > /root/.ssh/config
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel ERROR
    IdentityFile /root/.ssh/mutagen_id
    Port ${MUTAGEN_SSH_PORT}
EOF
fi

create_session() {
    local name="$1"
    local source="$2"
    local dest="$3"

    set +e
    mutagen sync list 2>/dev/null | grep -q "Name: ${name}"
    local exists=$?
    set -e

    if [ "$exists" -eq 0 ]; then
        echo "Mutagen session already exists: ${name}"
        return
    fi

    echo "Creating mutagen session: ${name}"
    mutagen sync create \
        --name "${name}" \
        --mode "${MUTAGEN_SYNC_MODE}" \
        --no-ignore-vcs \
        --ignore ".venv" \
        --ignore "node_modules" \
        --ignore ".git" \
        "${source}" \
        "${dest}"
}

MUTAGEN_BACKEND_USER="${MUTAGEN_BACKEND_USER:-python}"
MUTAGEN_FRONTEND_USER="${MUTAGEN_FRONTEND_USER:-node}"

for target in ${BACKEND_TARGETS}; do
    create_session "backend-${target}" \
        "${MUTAGEN_SOURCE_ROOT}/backend" \
        "${MUTAGEN_BACKEND_USER}@${target}:/app/backend"
 done

for target in ${FRONTEND_TARGETS}; do
    create_session "frontend-${target}" \
        "${MUTAGEN_SOURCE_ROOT}/frontend" \
        "${MUTAGEN_FRONTEND_USER}@${target}:/app/frontend"
 done
