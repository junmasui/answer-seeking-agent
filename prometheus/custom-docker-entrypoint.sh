#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
# set -o pipefail  # Use right-most non-zero exit code from a pipe.

# # Set environment variables from mounted secrets files

# set +o history # temporarily turn off history
# SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# # shellcheck disable=SC2046
# export $( grep -h -v "^#" ${SECRETS_MOUNT}/*_env | xargs -n1 )
# set -o history # turn it back on


WAIT_LIMIT=300
WAIT_INTERVAL=5
ELAPSED=0

echo "Waiting for alertmanager server to be ready..."
until [ $ELAPSED -ge $WAIT_LIMIT ]
do
    sleep $WAIT_INTERVAL
    # The $((...)) syntax is for shell arithematic operations.
    ELAPSED=$(( ELAPSED + WAIT_INTERVAL ))
    ( wget -qS -O - http://alertmanager:9093/-/healthy 2>&1 ) \
            | grep -q 'HTTP/1.1 200 OK'
    RESULT=$?
    echo result $RESULT
    if [ $RESULT == 0 ]
    then
        echo "alertmanager server started."
        break
    fi
done

if [ $ELAPSED -ge $WAIT_LIMIT ]; then
  echo "alertmanager server did not start within ${WAIT_LIMIT} seconds."
  exit 1
fi


# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   podman image inspect prom/prometheus | jq '.[0].Config.Entrypoint'
exec /bin/prometheus "$@"
