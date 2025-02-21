#!/usr/bin/env bash

if [ -z "$COMPOSE_FILE" ]
then
    echo "set environment variable COMPOSE_FILE"
    exit 1
fi

if [ -z "$COMPOSE_PROFILES" ]
then
    echo "set environment variable COMPOSE_PROFILES to all"
    exit 1
fi

# Start up the system.
#
docker compose --profile infrastructure up -d
docker compose --profile backend up -d
docker compose --profile frontend --profile backend up -d


for LOOP in {1..10}
do
    ./display_processes.sh
    if [ $? -eq 0 ]
    then
        break
    fi
    sleep 5
done
