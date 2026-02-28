#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

#
# Interactive launcher for dev-tools container
#
# This script provides a convenient way to run the dev-tools container
# interactively without needing Docker Compose.
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
            echo "  --gpu-mode=MODE    GPU mode: cpu or cuda12 (default: cpu)"
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
if [[ "$GPU_MODE" != "cpu" && "$GPU_MODE" != "cuda12" ]]; then
    echo "Error: Invalid GPU mode '$GPU_MODE'. Must be 'cpu' or 'cuda12'" >&2
    exit 1
fi

# Determine image tag based on GPU mode
if [[ "$GPU_MODE" == "cuda12" ]]; then
    IMAGE_TAG="localhost/localhost/answers-dev-tools:python-3.12-cuda12"
else
    IMAGE_TAG="localhost/localhost/answers-dev-tools:python-3.12-cpu"
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

# Get user/group ID from environment or current user
RUN_AS_UID="${DEV_UID:-$(id -u)}"
RUN_AS_GID="${DEV_GID:-$(id -g)}"

# Determine repository root (parent directory of dev-tools)
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Build docker run command
DOCKER_ARGS=(
    "run"
    "--name" "$CONTAINER_NAME"
    "--user" "root"
    "--privileged"
    "--network" "agent_agent-poc"
    "-e" "GPU_MODE=$GPU_MODE"
    "-e" "RUN_AS_UID=$RUN_AS_UID"
    "-e" "RUN_AS_GID=$RUN_AS_GID"
    "-e" "USE_CODEBASE_SYNC=false"
    "-e" "USE_BOOTSTRAP_INSTALL=true"
    "-e" "ENABLE_SSHD=false"
    "-e" "ENABLE_MUTAGEN_SYNC=false"
    "-e" "PYTHONPYCACHEPREFIX=/home/python/.pycache"
    "-v" "$REPO_ROOT:/app"
    "-v" "dev-tools-venv:/app/backend/.venv"
    "-v" "dev-tools-node-modules:/app/frontend/node_modules"
    "-v" "/var/run/docker.sock:/var/run/docker.sock:ro"
)

# Add GPU support if needed
if [[ "$GPU_MODE" == "cuda12" ]]; then
    DOCKER_ARGS+=(
        "--gpus" "all"
    )
fi

# Add interactive/detach flags
if [[ "$DETACH_MODE" == true ]]; then
    DOCKER_ARGS+=("-d")
    COMMAND=("sleep" "infinity")
    echo "Starting dev-tools container in detached mode..."
else
    DOCKER_ARGS+=("-it")
    COMMAND=("bash")
    echo "Starting interactive dev-tools container..."
fi

# Add image and command
DOCKER_ARGS+=("$IMAGE_TAG")
DOCKER_ARGS+=("${COMMAND[@]}")

# Run the container
docker "${DOCKER_ARGS[@]}"

if [[ "$DETACH_MODE" == true ]]; then
    echo ""
    echo "Container started successfully!"
    echo "To attach to the container, run:"
    echo "  docker exec -it $CONTAINER_NAME bash"
    echo ""
    echo "To stop the container, run:"
    echo "  docker rm -f $CONTAINER_NAME"
fi
