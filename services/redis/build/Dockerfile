FROM redis:7.4.1-bookworm

ARG NONPRIV_USER=redis

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    gosu; \
    rm -rf /var/lib/apt/lists/*; \
    # verify that the binary works
    gosu nobody true

COPY --from=config-dir /custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir /custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh

RUN chmod +x /custom-docker-entrypoint.sh /custom-docker-entrypoint-nonpriv.sh

ENTRYPOINT ["/custom-docker-entrypoint.sh"]
CMD ["redis-server", "/redis.conf"]
