#!/usr/bin/env bash

# Set environment variables from mounted secrets files
SECRETS_MOUNT="${SECRETS_MOUNT:-/run/secrets}"
# shellcheck disable=SC2046
export $( grep -h -v "^#" "${SECRETS_MOUNT}"/*_secrets | xargs -n1 )

# The nemoguardrails application needs these directories to exist: 
mkdir -p /app/examples/bots
mkdir -p /app/chat-ui/frontend

apt-get update && apt-get install -y curl

uv pip install /dist/core_telemetry_distro-0.1.0-py3-none-any.whl
uv pip install /dist/core_telemetry_instrumentation-0.1.0-py3-none-any.whl

uv add langchain-openai

# Process with original entrypoint, which can be discovered
# from the host command-line with:
#   docker inspect nemoguardrails:latest | jq '.[0].Config.Entrypoint'
exec uv run opentelemetry-instrument nemoguardrails "$@"
