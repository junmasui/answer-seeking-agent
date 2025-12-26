#!/bin/sh
set -e

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

WAIT_LIMIT=300
WAIT_INTERVAL=5
ELAPSED=0

# Using weed shell to check readiness and create bucket.
# We connect to localhost:9333 (Master) since we are in the network or via the entrypoint logic.
# However, this script runs in 'seaweedfs-init' container.
# We need to talk to 'seaweedfs' host.
# 'weed shell' connects to master.
# Command: weed shell -master=seaweedfs:9333 -command "..."

echo "Waiting for SeaweedFS Master to be ready..."

until weed shell -master=seaweedfs:9333 -command "remote.mount -list" > /dev/null 2>&1 \
      || [ "$ELAPSED" -ge "$WAIT_LIMIT" ]; do
  sleep "$WAIT_INTERVAL"
  ELAPSED=$((ELAPSED + WAIT_INTERVAL))
done

if [ "$ELAPSED" -ge "$WAIT_LIMIT" ]; then
  echo "SeaweedFS Master did not start within ${WAIT_LIMIT} seconds."
  exit 1
fi

echo "Initializing SeaweedFS bucket ${SEAWEEDFS_BUCKET}..."

# Create bucket using weed shell
# s3.bucket.create is the command
weed shell -master=seaweedfs:9333 -command "s3.bucket.create -name=${SEAWEEDFS_BUCKET}"

echo "Detailed setup done."

echo "Detailed setup done."
