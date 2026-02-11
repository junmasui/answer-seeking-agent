#!/usr/bin/env bash

# Use the directory of the script to determine relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set local Dagster home
export DAGSTER_HOME="$SCRIPT_DIR/.dagster"
echo "Using DAGSTER_HOME=$DAGSTER_HOME"

# Switch to the script directory to run commands
cd "$SCRIPT_DIR"

# Run the Dagster development server (webserver + daemon)
uv run dagster dev
