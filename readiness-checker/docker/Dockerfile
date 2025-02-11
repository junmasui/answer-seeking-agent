FROM debian:12.9-slim

#
# Locally required Debian packages
#

RUN apt-get update \
    && apt-get install -y \
        curl \
        bind9-dnsutils \
        redis-tools \
        postgresql-client-common \
        postgresql-client-15 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
