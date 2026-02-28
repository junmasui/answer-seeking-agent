#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

echo "Initializing dev-tools volumes..."

RUN_AS_UID="${RUN_AS_UID:-1000}"
RUN_AS_GID="${RUN_AS_GID:-1000}"

# Ensure user exists and configure passwordless sudo
if ! id -u "${RUN_AS_UID}" >/dev/null 2>&1; then
    echo "Creating user with UID ${RUN_AS_UID}..."
    # Create group if it doesn't exist
    if ! getent group "${RUN_AS_GID}" >/dev/null 2>&1; then
        groupadd -g "${RUN_AS_GID}" devuser
    fi
    # Create user
    useradd -u "${RUN_AS_UID}" -g "${RUN_AS_GID}" -m -s /bin/bash devuser
fi

# Get username for the UID
USERNAME=$(id -un "${RUN_AS_UID}")
echo "Configuring passwordless sudo for user ${USERNAME} (UID ${RUN_AS_UID})..."
echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}"
chmod 0440 "/etc/sudoers.d/${USERNAME}"

# Fix ownership of mounted volumes
if [ -d /app/backend/.venv ]; then
    echo "Fixing ownership of /app/backend/.venv..."
    chown -R "${RUN_AS_UID}:${RUN_AS_GID}" /app/backend/.venv
fi

if [ -d /app/frontend/node_modules ]; then
    echo "Fixing ownership of /app/frontend/node_modules..."
    chown -R "${RUN_AS_UID}:${RUN_AS_GID}" /app/frontend/node_modules
fi

echo "Dropping privileges to UID ${RUN_AS_UID}..."
exec gosu "${RUN_AS_UID}:${RUN_AS_GID}" /custom-docker-entrypoint-nonpriv.sh "$@"
