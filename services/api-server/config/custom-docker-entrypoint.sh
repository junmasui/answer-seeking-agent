#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from secrets
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

  # Configure SSH for python user (UID 1000) if it exists
  if id -u python >/dev/null 2>&1; then
      SSH_USER_HOME="/home/python"
      SSH_USER="python"
      SSH_GROUP="python"
  else
      # Fallback to root if python user doesn't exist (unexpected in this container)
      SSH_USER_HOME="/root"
      SSH_USER="root"
      SSH_GROUP="root"
  fi

  mkdir -p /var/run/sshd "${SSH_USER_HOME}/.ssh"
  chmod 700 "${SSH_USER_HOME}/.ssh"

  if [ -f "/run/secrets/mutagen_sshd_authorized_keys" ]; then
    cp /run/secrets/mutagen_sshd_authorized_keys "${SSH_USER_HOME}/.ssh/authorized_keys"
    chmod 600 "${SSH_USER_HOME}/.ssh/authorized_keys"
    chown -R "${SSH_USER}:${SSH_GROUP}" "${SSH_USER_HOME}/.ssh"
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

# Volume initialization logic (must run as root)
echo "Initializing backend volumes..."

# Runtime service orchestration is handled without FUSE mounts.

start_sshd

echo "Running in Standard mode (Mutagen sync)..."

API_VOLS="/staging"

for VOL in $API_VOLS
do
  if [ -d "$VOL" ]; then
    if grep -q " $VOL " /proc/self/mounts; then
      if [ ! -f "$VOL/.initialized" ]; then
        echo "Initializing $VOL..."
        touch "$VOL/.initialized"
        chown -R 1000:1000 "$VOL"
        chmod -R 755 "$VOL"
        ls -ld "$VOL"
      else
        echo "$VOL is already initialized."
      fi
    else
      echo "$VOL is part of the image, skipping initialization."
    fi
  fi
done

echo "Dropping privileges to python (UID 1000)..."
exec gosu 1000:1000 /custom-docker-entrypoint-nonpriv.sh "$@"
