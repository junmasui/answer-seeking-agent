FROM docker.io/postgres:17.5-bookworm

ENV DEBIAN_FRONTEND=noninteractive
RUN \
  apt-get update \
  && apt-get --no-install-recommends install -y ca-certificates curl gettext-base \
  #
  # Install pgvector
  #
  && curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail --proto "=https" --proto-redir "=https" https://www.postgresql.org/media/keys/ACCC4CF8.asc \
  && apt-get --no-install-recommends install -y postgresql-17-pgvector \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

