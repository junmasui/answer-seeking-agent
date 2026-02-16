#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

echo "Initializing dev-tools volumes..."

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

start_sshd

RUN_AS_UID="${RUN_AS_UID:-1000}"
RUN_AS_GID="${RUN_AS_GID:-1000}"

echo "Dropping privileges to UID ${RUN_AS_UID}..."
exec gosu "${RUN_AS_UID}:${RUN_AS_GID}" /custom-docker-entrypoint-nonpriv.sh "$@"
