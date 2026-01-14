#!/bin/sh
set -e

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
for FILE in "${SECRETS_MOUNT}"/*_secrets
do
    [ -f "$FILE" ] || continue
    # We can't use the file descriptor trick easily if we want to export to current shell 
    # and then run envsubst in the same shell context for the template.
    # But since we are likely replacing the shell process with exec, we need these vars.
    # The pure-shell loop is safer for secrets.
    
    while IFS='=' read -r KEY VALUE || [ -n "$KEY" ]; do
      case "$KEY" in
        \#* | '') continue ;;
        *) export "$KEY=$VALUE" ;;
      esac
    done < "$FILE"
done

# Ensure SEAWEEDFS environment variables are set to avoid duplicate keys in s3.json
if [ -z "$SEAWEEDFS_ROOT_USER" ]; then
    # Fallback to S3_ACCESS_KEY or default to 'admin'
    export SEAWEEDFS_ROOT_USER="${S3_ACCESS_KEY:-admin}"
fi
if [ -z "$SEAWEEDFS_ROOT_PASSWORD" ]; then
    # Fallback to S3_SECRET_KEY. If neither is set, let the next check fail it.
    export SEAWEEDFS_ROOT_PASSWORD="${S3_SECRET_KEY}"
fi
if [ -z "$SEAWEEDFS_ROOT_PASSWORD" ]; then
    echo "ERROR: SEAWEEDFS_ROOT_PASSWORD is not set."
    exit 1
fi

# Generate s3.json from template
if [ -f "/etc/seaweedfs/s3.json.template" ]; then
    echo "Generating /etc/seaweedfs/s3.json from template..."
    envsubst < /etc/seaweedfs/s3.json.template > /etc/seaweedfs/s3.json
fi

# Pass arguments to the original entrypoint or run weed command directly
# Official image entrypoint is usually just the binary or a script. 
# We simply exec the command provided as CMD in compose or default to weed server.

echo "Starting SeaweedFS S3..."
exec weed "$@"
