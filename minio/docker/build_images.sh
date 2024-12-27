docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --no-cache \
  --tag localdomain-minio:2024-12-13T22-19-12Z-cpuv1 \
  .
