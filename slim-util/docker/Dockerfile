FROM docker.io/debian:12.9-slim

#
# Locally required Debian packages
#

RUN apt-get update \
    && apt-get install -y \
        bind9-dnsutils \
        curl \
        gettext-base \
        postgresql-client-common \
        postgresql-client-15 \
        procps \
        redis-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT [ "bash" ]
