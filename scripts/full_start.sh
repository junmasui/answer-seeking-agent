#!/usr/bin/env bash

GPU_MODE="$1"

if [ -z "${GPU_MODE:-}" ]
then
    echo "GPU mode missing"
    exit 1
fi

if [ "$GPU_MODE" == "cuda12" ]; then
    export COMPOSE_FILE=common.compose.yml:cuda.compose.yml
elif [ "$GPU_MODE" == "cpu" ]; then
    export COMPOSE_FILE=common.compose.yml:cpu-only.compose.yml
else
    echo "invalid GPU mode: ${GPU_MODE}"
    exit 1
fi

./scripts/pull_images.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error pulling public images"
    exit -1
fi

./scripts/build_images.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error building images"
    exit -1
fi

./scripts/build_python_packages.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error building Python packages"
    exit -1
fi

./scripts/update_secrets.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error setting up docker compose secrets"
    exit -1
fi

./scripts/launch_services.sh $GPU_MODE

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error launching. Retrying"

    ./scripts/launch_services.sh $GPU_MODE

    EXIT_CODE="$?"
    if [ "$EXIT_CODE" != 0 ]
    then
        echo "Error launching."
        exit -1
    fi
fi


./display_processes.sh $GPU_MODE
