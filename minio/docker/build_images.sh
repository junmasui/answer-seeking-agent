docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --progress=plain \
  --tag localdomain-minio:2024-12-13T22-19-12Z \
  .
