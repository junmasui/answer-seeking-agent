FROM traefik:v3.4

ARG NONPRIV_USER=traefik

USER root

# Traefik image is Alpine-based.
RUN apk add --no-cache gosu || \
    (apk add --no-cache curl gnupg && \
    curl -L https://github.com/tianon/gosu/releases/download/1.17/gosu-amd64 -o /usr/local/bin/gosu && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true)

COPY --from=config-dir /custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir /custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh

RUN chmod +x /custom-docker-entrypoint.sh /custom-docker-entrypoint-nonpriv.sh

ENTRYPOINT ["/custom-docker-entrypoint.sh"]
CMD ["traefik"]
