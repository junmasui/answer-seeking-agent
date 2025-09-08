FROM docker.io/debian:12.9-slim

#
# Locally required Debian packages
#

RUN apt-get update \
    && apt-get --no-install-recommends install -y \
        bind9-dnsutils \
        curl \
        gettext-base \
        postgresql-client-15 \
        postgresql-client-common \
        procps \
        redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "bash" ]
