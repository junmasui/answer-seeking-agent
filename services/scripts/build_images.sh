#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Build container images.
for SUBDIR in slim-util nemo api-server webui-server
do
    ( cd "$SUBDIR"/build ; ./build_images.sh )
done

