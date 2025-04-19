FROM docker.io/postgres:17.2-bookworm

RUN apt-get update \
  && apt-get install -y gettext-base curl ca-certificates

# Install pgvector
RUN curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-17-pgvector \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

