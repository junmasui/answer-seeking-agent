#
# Builds the customized Clickhouse image.
#
# NOTE: Use environment variables BUILDKIT_PROGRESS, BUILDKIT_COLOR, etc to
#       control the progress output.
# NOTE: Use `docker builder prune` to clean up the build cache.
#
docker buildx build \
  --build-context parent-dir=.. \
  --file Dockerfile \
  --tag localdomain-postgres:17.2-pgvector \
  .
