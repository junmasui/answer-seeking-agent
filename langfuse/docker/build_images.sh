docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --progress=plain \
  --tag localhost/localdomain-langfuse:3.24 \
  .
