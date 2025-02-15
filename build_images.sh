#!/usr/bin/env bash

set -eu

for SUBDIR in postgres start-gate langfuse frontend backend
do
    ( cd $SUBDIR/docker ; ./build_images.sh )
done

