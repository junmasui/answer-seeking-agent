#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Build a general image that is based on the official Python 3.12 on Debian 12 (Bookworm)
# with CUDA 12 and CUDNN 9 installed.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

# DOCKER=podman
DOCKER="docker buildx"
#DOCKER_BUILD_OPTS="--no-cache"
DOCKER_BUILD_OPTS=

#
# Build an image with CUDA12 installed on Python 3.12 on Debian 12
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file cuda12.Dockerfile \
  --target python3.12-cuda12-cudnn9 \
  --tag localhost/localhost/python:3.12.10-bookworm-cuda12-cudnn9 \
  . 2>&1 \
| tee build-python-bookworm-cuda12-cudnn9.log

#
# Build a backend image with Python 3.12 on Debian 12
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config \
  --build-context celery-config-dir=../../celery-worker/config \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context src-dir=../../../backend \
  --target production \
  --tag localhost/localhost/answers-backend:python-3.12-cpu \
  . 2>&1 \
| tee build-backend-python-cpu.log

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file Dockerfile \
  --build-context config-dir=../config \
  --build-context celery-config-dir=../../celery-worker/config \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context src-dir=../../../backend \
  --target dev \
  --tag localhost/localhost/answers-backend-dev:python-3.12-cpu \
  . 2>&1 \
| tee build-backend-dev-python-cpu.log


#
# Build a backend image with Python 3.12 on Debian 12 with CUDA 12
#
$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file cuda12.Dockerfile \
  --build-context config-dir=../config \
  --build-context celery-config-dir=../../celery-worker/config \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context src-dir=../../../backend \
  --target production \
  --tag localhost/localhost/answers-backend:python-3.12-cuda12 \
  . 2>&1 \
| tee build-backend-python-cuda12.log

$DOCKER build \
  $DOCKER_BUILD_OPTS \
  --file cuda12.Dockerfile \
  --build-context config-dir=../config \
  --build-context celery-config-dir=../../celery-worker/config \
  --build-context dependency-gate-dir=../../dependency-gate \
  --build-context src-dir=../../../backend \
  --target dev \
  --tag localhost/localhost/answers-backend-dev:python-3.12-cuda12 \
  . 2>&1 \
| tee build-backend-dev-python-cuda12.log
