#!/usr/bin/env bash

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# The minio/minio image does not include the Debian findutil and grep packages.
# Hence we need to use a pure-shell alternative to our more frequent technique
# of `export $( grep | xargs )`
for FILE in "${SECRETS_MOUNT}"/*_secrets
do
    [ -f "$FILE" ] || continue
    exec 3< "$FILE" # Open file descriptor 3. This robustly avoids subshell issues.
    while IFS='=' read -r KEY VALUE <&3  # Read from file descriptor 3.
    do
        case "$KEY" in
            # Skips comments and empty lines.
            \#* | '') continue ;;
            # Sets environment variables.
            *) export "$KEY=$VALUE" ;;
        esac
    done
    exec 3<&- # Close file descriptor 3.
done

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect minio/minio:RELEASE.2024-12-13T22-19-12Z | jq '.[0].Config.Entrypoint'
exec /usr/bin/docker-entrypoint.sh "$@"
