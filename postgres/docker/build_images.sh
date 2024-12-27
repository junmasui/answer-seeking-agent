docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --no-cache \
  --tag localdomain-postgres:17.2-pgvector \
  .
