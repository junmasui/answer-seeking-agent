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

#
# Build an image with CUDA12 installed on Python 3.12 on Debian 12
#
$DOCKER build \
  --file python_bookworm_cuda12.Dockerfile \
  --tag localhost/localhost/python:3.12.10-bookworm-cuda12-cudnn9 \
  . 2>&1 \
| tee build-python-bookworm-cuda12-cudnn9.log

#
# Build a backend image with Python 3.12 on Debian 12
#
$DOCKER build \
  --no-cache \
  --file Dockerfile \
  --build-context parent-dir=.. \
  --build-context dependency-gate-dir=../../dependency-gate \
  --tag localhost/localhost/answers-backend:python-3.12-cpu \
  . 2>&1 \
| tee build-backend-python-cpu.log

$DOCKER build \
  --no-cache \
  --file dev.Dockerfile \
  --build-context parent-dir=.. \
  --tag localhost/localhost/answers-backend-dev:python-3.12-cpu \
  . 2>&1 \
| tee build-backend-dev-python-cpu.log


#
# Build a backend image with Python 3.12 on Debian 12 with CUDA 12
#
$DOCKER build \
  --no-cache \
  --file cuda12.Dockerfile \
  --build-context parent-dir=.. \
  --build-context dependency-gate-dir=../../dependency-gate \
  --tag localhost/localhost/answers-backend:python-3.12-cuda12 \
  . 2>&1 \
| tee build-backend-python-cuda12.log

$DOCKER build \
  --no-cache \
  --file dev_cuda12.Dockerfile \
  --build-context parent-dir=.. \
  --tag localhost/localhost/answers-backend-dev:python-3.12-cuda12 \
  . 2>&1 \
| tee build-backend-dev-python-cuda12.log
