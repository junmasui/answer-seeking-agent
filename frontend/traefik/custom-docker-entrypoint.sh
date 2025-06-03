#!/usr/bin/env sh

## set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
## set -o pipefail  # Use right-most non-zero exit code from a pipe.


touch /acme/acme.json
chmod 600 /acme/acme.json

echo exec /entrypoint.sh "$@"

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect traefik:v3.4 | jq '.[0].Config.Entrypoint'
exec /entrypoint.sh "$@"
