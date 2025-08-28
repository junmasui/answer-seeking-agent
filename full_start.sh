#!/usr/bin/env bash

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

./scripts/launch_services.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error launching. Retrying"

    ./scripts/launch_services.sh

    EXIT_CODE="$?"
    if [ "$EXIT_CODE" != 0 ]
    then
        echo "Error launching."
        exit -1
    fi
fi


./display_processes.sh
