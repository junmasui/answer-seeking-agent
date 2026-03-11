#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Interactive launcher for dev-tools container
#
# This script provides a convenient way to run the dev-tools container
# interactively using Docker Compose.
#

# Default values
GPU_MODE="cpu"
DETACH_MODE=false
CONTAINER_NAME="dev-tools-interactive"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --gpu-mode=*)
            GPU_MODE="${1#*=}"
            ;;
        --detach)
            DETACH_MODE=true
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --gpu-mode=MODE    GPU mode: cpu or cuda13 (default: cpu)"
            echo "  --detach           Run container in background (detached mode)"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
    shift
done

# Validate GPU mode
if [[ "$GPU_MODE" != "cpu" && "$GPU_MODE" != "cuda13" ]]; then
    echo "Error: Invalid GPU mode '$GPU_MODE'. Must be 'cpu' or 'cuda13'" >&2
    exit 1
fi

# Determine image tag and compose override based on GPU mode
if [[ "$GPU_MODE" == "cuda13" ]]; then
    IMAGE_TAG="localhost/localhost/agent-dev-tools:python-3.12-cuda13"
    COMPOSE_OVERRIDE="cuda.compose.yml"
else
    IMAGE_TAG="localhost/localhost/agent-dev-tools:python-3.12-cpu"
    COMPOSE_OVERRIDE="cpu-only.compose.yml"
fi

# Check if image exists
if ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
    echo "Error: Docker image '$IMAGE_TAG' not found" >&2
    echo "" >&2
    echo "Please build the image first:" >&2
    echo "  cd dev-tools/build" >&2
    echo "  ./build_images.sh" >&2
    exit 1
fi

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Container '$CONTAINER_NAME' already exists."
    read -p "Do you want to remove it and create a new one? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing container..."
        docker rm -f "$CONTAINER_NAME"
    else
        echo "Aborted. Use 'docker exec -it $CONTAINER_NAME bash' to attach to the existing container."
        exit 0
    fi
fi

# Export user/group ID for compose interpolation
export DEV_UID="${DEV_UID:-$(id -u)}"
export DEV_GID="${DEV_GID:-$(id -g)}"

# Change to compose file directory so relative paths in compose files resolve correctly
cd "$(dirname "$0")/deploy"

COMPOSE=(docker compose -f common.compose.yml -f "$COMPOSE_OVERRIDE")

if [[ "$DETACH_MODE" == true ]]; then
    echo "Starting dev-tools container in detached mode..."
    "${COMPOSE[@]}" run -d --name "$CONTAINER_NAME" dev-tools sleep infinity
    echo ""
    echo "Container started successfully!"
    echo "To attach to the container, run:"
    echo "  docker exec -it $CONTAINER_NAME bash"
    echo ""
    echo "To stop the container, run:"
    echo "  docker rm -f $CONTAINER_NAME"
else
    echo "Starting interactive dev-tools container..."
    "${COMPOSE[@]}" run --name "$CONTAINER_NAME" dev-tools bash
fi
