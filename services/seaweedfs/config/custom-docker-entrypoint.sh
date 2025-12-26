#!/bin/bash
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

# Ensure SEAWEEDFS_BUCKET is set
# We still keep this fallback or assume users provide SEAWEEDFS_BUCKET in secrets?
# The user said "secrets files will also have the corrected the environment variable names".
# So we can remove the fallback logic too if we want to be strict, but keeping a check doesn't hurt.
# However, the user specifically mentioned "no need to remap".
# I will just remove the explicit remapping case block.

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
