FROM docker.io/debian:12.10-slim

#
# Locally required Debian packages
#

RUN apt-get update \
    && apt-get install -y \
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
