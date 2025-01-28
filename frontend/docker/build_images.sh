

docker buildx build \
  --build-context parent-dir=.. \
  --no-cache \
  --tag localdomain-frontend:node-22-bookworm \
  .

docker buildx build \
  --file nginx.Dockerfile \
  --no-cache \
  --tag localdomain-nginx:1.27-bookworm \
  .
