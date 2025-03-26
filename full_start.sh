#!/usr/bin/env bash

./build_images.sh

EXIT_CODE=$?
echo "build with " $EXIT_CODE
if [ $EXIT_CODE != 0 ]
then
    echo "Error building images"
    exit -1
fi

./setup_rootless.sh

EXIT_CODE=$?
if [ $EXIT_CODE != 0 ]
then
    echo "Error setting up for rootless docker"
    exit -1
fi

./update_secrets.sh

EXIT_CODE=$?
if [ $EXIT_CODE != 0 ]
then
    echo "Error setting up docker compose secrets"
    exit -1
fi

./launch_services.sh

EXIT_CODE=$?
if [ $EXIT_CODE != 0 ]
then
    echo "Error launching. Retrying"
fi

docker compose up -d langfuse-worker

./launch_services.sh

EXIT_CODE=$?
if [ $EXIT_CODE != 0 ]
then
    echo "Error launching."
    exit -1
fi

./display_processes.sh
