#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

# Build container images.
for SUBDIR in slim-util seaweedfs redis opensearch traefik weaviate api-server
do
    ( cd "$SUBDIR"/build ; ./build_images.sh )
done

# Build Python distributions.
./scripts/build_python_packages.sh

EXIT_CODE="$?"
if [ "$EXIT_CODE" != 0 ]
then
    echo "Error building Python packages"
    exit -1
fi

# Build container images.
for SUBDIR in nemo webui-server dev-server
do
    ( cd "$SUBDIR"/build ; ./build_images.sh )
done

