#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

echo "Initializing dev-server volumes..."

start_sshd() {
    if [ "${ENABLE_SSHD:-false}" != "true" ]; then
        return
    fi

    if ! command -v sshd >/dev/null 2>&1; then
        echo "Installing openssh-server..."
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get install -y --no-install-recommends openssh-server
        rm -rf /var/lib/apt/lists/*
    fi

    mkdir -p /var/run/sshd /root/.ssh
    chmod 700 /root/.ssh

    if [ -f "/run/secrets/mutagen_sshd_authorized_keys" ]; then
        cp /run/secrets/mutagen_sshd_authorized_keys /root/.ssh/authorized_keys
        chmod 600 /root/.ssh/authorized_keys
    fi

    if [ ! -f /etc/ssh/sshd_config ]; then
        cat <<'EOF' > /etc/ssh/sshd_config
Port 22
Protocol 2
PermitRootLogin prohibit-password
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
EOF
    fi

    echo "Starting sshd..."
    /usr/sbin/sshd
}

start_mutagen_sync() {
    if [ "${ENABLE_MUTAGEN_SYNC:-false}" != "true" ]; then
        return
    fi

    if ! command -v mutagen >/dev/null 2>&1; then
        echo "Installing mutagen client..."
        MUTAGEN_VERSION="${MUTAGEN_VERSION:-0.18.1}"
        curl -fsSL "https://github.com/mutagen-io/mutagen/releases/download/v${MUTAGEN_VERSION}/mutagen_linux_amd64_v${MUTAGEN_VERSION}.tar.gz" \
            | tar -xz -C /usr/local/bin mutagen
        chmod +x /usr/local/bin/mutagen
    fi

    if [ -f /start_mutagen_sync.sh ]; then
        echo "Starting mutagen sync sessions..."
        bash /start_mutagen_sync.sh || echo "Warning: mutagen sync setup failed."
    fi
}

start_sshd
start_mutagen_sync

RUN_AS_UID="${RUN_AS_UID:-1000}"
RUN_AS_GID="${RUN_AS_GID:-1000}"

echo "Dropping privileges to UID ${RUN_AS_UID}..."
exec gosu "${RUN_AS_UID}:${RUN_AS_GID}" /custom-docker-entrypoint-nonpriv.sh "$@"
