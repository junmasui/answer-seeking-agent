FROM cr.weaviate.io/semitechnologies/weaviate:1.30.3

ARG NONPRIV_USER=weaviate

USER root

# Install gosu. Weaviate is Alpine-based.
RUN apk add --no-cache gosu || \
    (apk add --no-cache curl gnupg && \
    curl -L https://github.com/tianon/gosu/releases/download/1.17/gosu-amd64 -o /usr/local/bin/gosu && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true)

COPY --from=config-dir /custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir /custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh

RUN chmod +x /custom-docker-entrypoint.sh /custom-docker-entrypoint-nonpriv.sh

ENTRYPOINT ["/custom-docker-entrypoint.sh"]
# Original command from compose
CMD ["--host", "0.0.0.0", "--port", "25080", "--scheme", "http"]
