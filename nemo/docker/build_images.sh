#!/usr/bin/env bash

set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

if [ -d nemoguardrails ]
then
    rm -rf nemoguardrails
fi


#
# See: https://docs.nvidia.com/nemo/guardrails/latest/user-guides/advanced/using-docker.html#build-the-docker-images
#

git clone https://github.com/NVIDIA/NeMo-Guardrails.git nemoguardrails

(
cd nemoguardrails
docker build -f ../Dockerfile --build-context parent-dir=.. -t nemo-guardrails --progress plain .
)

# (
# cd nemoguardrails/library/jailbreak_detection
# docker build -t nemo-jailbreak-detection-heuristics .
# docker build -t nemo-jailbreak-detection-heuristics-gpu .
# )