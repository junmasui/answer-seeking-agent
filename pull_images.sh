set -e  # Exit immediately on error.
set -u  # Unbound variables are errors.
set -o pipefail  # Use right-most non-zero exit code from a pipe.

docker pull python:3.12.8-slim-bookworm

docker tag clickhouse:24.12.3

docker pull node:22-bookworm-slim
docker pull nginx:1.27.3-bookworm


docker pull grafana/grafana

docker pull langfuse/langfuse:3.24
docker pull langfuse/langfuse-worker:3.24

docker pull minio/minio:RELEASE.2024-12-13T22-19-12Z

docker pull postgres:17.2-bookworm
docker pull prom/prometheus
docker pull prom/alertmanager
docker pull redis
