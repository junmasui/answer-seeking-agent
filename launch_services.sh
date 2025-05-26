#!/usr/bin/env bash

##set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

if [ -z "${COMPOSE_FILE:-}" ]
then
    echo "set environment variable COMPOSE_FILE"
    exit 1
fi

if [ -z "${COMPOSE_PROFILES:-}" ]
then
    echo "set environment variable COMPOSE_PROFILES to all"
    exit 1
fi

# Start up the system.
#
MAX_RETRIES=9
BACKOFF=1.5

docker compose --profile infrastructure up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./display_processes.sh
    if [ $? -eq 0 ]
    then
        break
    fi
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi


docker compose --profile backend up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./display_processes.sh
    if [ $? -eq 0 ]
    then
        break
    fi
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi

docker compose up -d
if [ $? -ne 0 ]
then
    exit "$?"
fi

SLEEP_TIME=2
for LOOP in $(seq 1 "$MAX_RETRIES")
do
    ./display_processes.sh
    if [ $? -eq 0 ]
    then
        break
    fi
    sleep "$SLEEP_TIME"
    SLEEP_TIME=$( echo "$BACKOFF * $SLEEP_TIME" | bc )
done
if [ $? -ne 0 ]
then
    exit "$?"
fi
