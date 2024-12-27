FROM postgres:17.2-bookworm

RUN apt-get update \
  && apt-get install -y gettext-base curl ca-certificates

# Install pgvector
RUN curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-17-pgvector \
  && apt-get clean

# This script lives in the parent of the current directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1
COPY --from=parent-dir init-db.sql.template /
COPY --from=parent-dir init-postgres.sh /
RUN chmod +x /init-postgres.sh

