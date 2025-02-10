#!/usr/bin/env bash

set -eu

#
# Build a general image that is based on the official Python 3.12 on Debian 12 (Bookworm)
# with CUDA 12 and CUDNN 9 installed.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#

docker buildx build \
  --file python_bookworm_cuda12.Dockerfile \
  --tag localdomain-python:3.12.8-bookworm-cuda12-cudnn9 \
  . 2>&1 \
| tee build-python-bookworm-cuda12-cudnn9.log

#
# Build a backend image with Python 3.12 on Debian 12
#
docker buildx build \
  --file Dockerfile \
  --build-context parent-dir=.. \
  --tag localdomain-backend:python-3.12-cpu \
  . 2>&1 \
| tee build-backend-python-cpu.log

#
# Build a backend image with Python 3.12 on Debian 12 with CUDA 12
#
docker buildx build \
  --file cuda12.Dockerfile \
  --build-context parent-dir=.. \
  --tag localdomain-backend:python-3.12-cuda12 \
  . 2>&1 \
| tee build-backend-python-cuda12.log
