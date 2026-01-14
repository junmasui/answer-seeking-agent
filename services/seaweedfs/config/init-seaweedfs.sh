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


#
#
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

if [ -z "$S3_ACCESS_KEY" ]; then
    # Default to 'agentic' if not set
    export S3_ACCESS_KEY="${S3_ACCESS_KEY:-agentic}"
fi
# Only check if password is not set (no fallback)
if [ -z "$S3_SECRET_KEY" ]; then
    echo "ERROR: S3_SECRET_KEY is not set."
    exit 1
fi

if [ -z "$S3_SECRET_KEY" ]; then
    echo "ERROR: S3_SECRET_KEY is not set."
    exit 1
fi

# Ensure they are not identical to prevent duplicate key errors if defaults collide
if [ "$SEAWEEDFS_ROOT_USER" = "$S3_ACCESS_KEY" ]; then
    echo "WARNING: Root user and App user have same name '$SEAWEEDFS_ROOT_USER'. Appending '-app' to app user."
    export S3_ACCESS_KEY="${S3_ACCESS_KEY}-app"
fi



echo "Detailed setup done."

# SeaweedFS initialization logic
FILER_URL="${SEAWEEDFS_FILER:-${S3_ENDPOINT_URL:-http://seaweedfs:9002}}"
MASTER_URL="${SEAWEEDFS_MASTER:-seaweedfs:9005}"
BUCKET_NAME="${S3_BUCKET_NAME:-documents}"

echo "Waiting for SeaweedFS Filer at ${FILER_URL}..."
until curl -s "${FILER_URL}" > /dev/null; do
  echo "Filer not ready, retrying in 2s..."
  sleep 2
done

echo "Creating bucket '${BUCKET_NAME}'..."
# In SeaweedFS, S3 buckets are just directories under /buckets/ in the filer
curl -s -X POST "${FILER_URL}/buckets/${BUCKET_NAME}/" > /dev/null

echo "Bucket '${BUCKET_NAME}' created or already exists."

# Configure IAM user and permissions
echo "Configuring IAM user '${S3_ACCESS_KEY}'..."
weed shell -master="${MASTER_URL}" <<EOF
s3.configure -apply -user "${S3_ACCESS_KEY}" -access_key "${S3_ACCESS_KEY}" -secret_key "${S3_SECRET_KEY}" -actions "Read,Write,List" -buckets "${BUCKET_NAME}"
s3.configure
s3.bucket.list
EOF

echo "Initialization complete."
