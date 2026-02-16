#!/bin/bash
set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
if [ -d "$SECRETS_MOUNT" ]; then
    # shellcheck disable=SC2046
    export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets 2>/dev/null | xargs -n1 ) || true
fi

# Wait for dependency-gate to open.
#
if [ -f /wait_for_gate.sh ]; then
    source /wait_for_gate.sh
    ##wait_for_dependency_gate /init-signal/backend-autotest-gate
fi

#
# Ensure we are in the backend directory for python builds
#
if [ -d "/app/backend" ]; then
    cd /app/backend

    if [ -n "${GPU_MODE:-}" ] && [ "${USE_BOOTSTRAP_INSTALL:-false}" = "true" ]; then
        if [ "$GPU_MODE" == "cuda12" ]; then
            nvidia-smi
        fi

        # NOTE: Run compile_requirements.sh after changes to dependencies
        #
        if [ "$GPU_MODE" == "cuda12" ]; then
            uv sync  --extra cuda12 --dev --all-packages
        elif [ "$GPU_MODE" == "cpu" ]; then
            uv sync  --extra cpu --dev --all-packages
        else
            exit -1
        fi
    fi

    # Build all workspace members
    echo "Building all workspace members..."
    pwd

    # List of workspace members from pyproject.toml
    workspace_members=(
        "apps/db_migration"
        "apps/core_app"
        "apps/core_worker"
        "libs/core"
        "libs/core_db"
        "libs/core_public"
        "libs/core_tasks"
        "libs/core_telemetry_distro"
        "libs/core_telemetry_instrumentation"
        "libs/early_init"
        "libs/log_config_monitor"
    )

    failed_builds=()
    successful_builds=()

    if [ -d /dist ]; then
        BUILD_OUTDIR="--out-dir /dist"
    else
        BUILD_OUTDIR=
    fi

    for member in "${workspace_members[@]}"; do
        if [ -f "$member/pyproject.toml" ]; then
            echo "Building $member..."
            uv build $BUILD_OUTDIR "$member"
            if [ $? -eq 0 ]; then
                echo "✓ Successfully built $member"
                successful_builds+=("$member")
            else
                echo "✗ Failed to build $member"
                failed_builds+=("$member")
            fi
            echo "---"
        else
            echo "⚠ Skipping $member (no pyproject.toml found)"
            failed_builds+=("$member (no pyproject.toml)")
        fi
    done

    echo "Build Summary:"
    echo "=============="
    echo "Successful builds (${#successful_builds[@]}):"
    for build in "${successful_builds[@]}"; do
        echo "  ✓ $build"
    done

    if [ ${#failed_builds[@]} -gt 0 ]; then
        echo "Failed builds (${#failed_builds[@]}):"
        for build in "${failed_builds[@]}"; do
            echo "  ✗ $build"
        done
        exit 1
    else
        echo "All python builds successful!"
    fi
fi

#
# ViteJS Build / Install
#
echo "Installing/Building ViteJS project..."
if [ -d "/app/frontend" ]; then
    cd /app/frontend
    
    if [ "${USE_BOOTSTRAP_INSTALL:-false}" = "true" ]; then
       # We assume 'npm install' might handle builds or we run a build script if needed.
       # Checks if node_modules exists, if not install.
       if [ ! -d "node_modules" ]; then
           echo "Installing npm dependencies in ../frontend..."
           echo npm install
       else
           echo "node_modules exists in ../frontend. Running npm install to ensure sync..."
           echo npm install
       fi
    fi

    # Optional: Run build if there is a build script
    # if jq -e '.scripts.build' package.json >/dev/null; then
    #     npm run build
    # fi
    
else
    echo "Warning: ../frontend directory not found. Skipping ViteJS build."
fi

echo "Environment setup complete."
echo "Sleeping infinitely to allow attachment..."

trap "echo 'Stopping...'; exit 0" SIGTERM SIGINT

while true; do
    sleep 3600 &
    wait $!
done
