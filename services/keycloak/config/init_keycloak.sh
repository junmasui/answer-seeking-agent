#!/bin/bash

# Set environment variables from mounted secrets files

SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

export KC_DB_PASSWORD="${KEYCLOAK_POSTGRES_USER_PASSWORD}"

apt update && apt install curl -y

#
# Wait for keycloak to be ready
#
echo "waiting for keycloak to be ready"
while true
do
    curl -f "http://keycloak:${KC_HOSTNAME_PORT}"
    if [ "$?" -eq 0 ]
    then
        echo "keycloak is live"
        break
    fi
    sleep 2
done

#
pip install python-keycloak && python /init_keycloak.py
