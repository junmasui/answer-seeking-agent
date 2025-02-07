docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --progress=plain \
  --tag localhost/localdomain-langfuse:3.24 \
  .

docker buildx build \
  --build-context parent-dir=.. \
  --file worker.Dockerfile \
  --progress=plain \
  --tag localhost/localdomain-langfuse-worker:3.24 \
  .
