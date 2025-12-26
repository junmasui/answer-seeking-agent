#!/bin/bash
set -e

# Change to the directory of this script
cd "$(dirname "$0")"

# Build the image
docker build -t localhost/localhost/seaweedfs:latest .
