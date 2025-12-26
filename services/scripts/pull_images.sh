set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

docker pull python:3.12.8-slim-bookworm

docker pull node:22-bookworm-slim

docker pull grafana/grafana:12.1.0

docker pull jaegertracing/all-in-one:1.74.0

docker pull mcr.microsoft.com/presidio-analyzer:2.2.360
docker pull mcr.microsoft.com/presidio-anonymizer:2.2.360
docker pull minio/minio:RELEASE.2025-09-07T16-13-09Z

docker pull opensearchproject/opensearch:2.17.1
docker pull otel/opentelemetry-collector-contrib:0.130.0

docker pull postgres:17.5-bookworm
docker pull prom/prometheus:v3.4.2
docker pull prom/alertmanager:v0.28.1

docker pull redis:7.4.1-bookworm

docker pull traefik:v3.4

docker pull cr.weaviate.io/semitechnologies/weaviate:1.30.3
