#!/usr/bin/env sh
## set -o pipefail  # Use right-most non-zero exit code from a pipe.

# NOTE: Alpine's sh shell does not keep command-line history by default.

# Set environment variables from mounted secrets files

SECRETS_MOUNT=${SECRETS_MOUNT:-/run/secrets}
# The weaviate image is based on Alpine.
# Hence we need to use a pure-shell alternative to our more frequent technique
# of `export $( grep | xargs )`
for FILE in ${SECRETS_MOUNT}/*_env
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

# List one or more keys in plaintext separated by commas. Each key corresponds to a specific user identity below.
export AUTHENTICATION_APIKEY_ALLOWED_KEYS="${WEAVIATE_USER_API_KEY}"

# List one or more user identities, separated by commas. Each identity corresponds to a specific key above.
export AUTHENTICATION_APIKEY_USERS="${WEAVIATE_USER_NAME}"


# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker image inspect cr.weaviate.io/semitechnologies/weaviate:1.30.3 | jq '.[0].Config.Entrypoint'
exec "/bin/weaviate" $@
