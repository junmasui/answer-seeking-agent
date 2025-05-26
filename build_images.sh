#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

for SUBDIR in postgres slim-util frontend backend
do
    ( cd "$SUBDIR"/docker ; ./build_images.sh )
done
