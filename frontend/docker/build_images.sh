

docker buildx build \
  --build-context parent-dir=.. \
  --no-cache \
  --tag localdomain-frontend:node-22-bookworm \
  .
