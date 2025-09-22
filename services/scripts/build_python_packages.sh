#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

export COMPOSE_FILE=common.compose.yml:cpu-only.compose.yml

# Build Python packages.
docker compose run --rm python-build
