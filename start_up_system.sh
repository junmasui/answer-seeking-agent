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


./display_processes.sh
