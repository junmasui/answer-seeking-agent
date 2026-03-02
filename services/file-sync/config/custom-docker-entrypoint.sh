#!/bin/bash
set -e

echo "Starting file-sync service..."

# Setup SSH configuration for mutagen
setup_ssh_config() {
    echo "Setting up SSH configuration..."

    mkdir -p ~/.ssh
    chmod 700 ~/.ssh

    # Copy SSH private key if provided
    if [ -f /run/secrets/mutagen_ssh_private_key ]; then
        cp /run/secrets/mutagen_ssh_private_key ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        echo "SSH private key configured"
    fi

    # Setup SSH config to disable strict host key checking for Docker containers
    cat > ~/.ssh/config <<EOF
Host *
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    LogLevel ERROR
EOF
    chmod 600 ~/.ssh/config

    echo "SSH configuration complete"
}

# Main entrypoint logic
main() {
    setup_ssh_config

    # Terminate any stale mutagen sessions from previous runs
    echo "Cleaning up stale mutagen sessions..."
    mutagen sync terminate --all 2>/dev/null || true

    echo "Starting supervisord..."
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
}

main "$@"
