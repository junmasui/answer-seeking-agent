#!/usr/bin/env bash
set -euo pipefail

# Mutagen sync does not require mount helpers. This script is kept for compatibility.
if [ "${USE_CODEBASE_SYNC:-false}" != "true" ]; then
    echo "Codebase sync not enabled. Helper exiting."
    exit 0
fi

echo "Mutagen codebase sync active. Mount helper not required."
exit 0
