FROM opensearchproject/opensearch:2.17.1

ARG NONPRIV_USER=1000:1000

USER root

# Install gosu. OpenSearch is usually AlmaLinux based.
RUN yum update -y --allowerasing && \
    yum install -y --allowerasing ca-certificates curl && \
    curl -L https://github.com/tianon/gosu/releases/download/1.17/gosu-amd64 -o /usr/local/bin/gosu && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true && \
    yum clean all && \
    rm -rf /var/cache/yum

COPY --from=config-dir /custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir /custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh

RUN chmod +x /custom-docker-entrypoint.sh /custom-docker-entrypoint-nonpriv.sh

ENTRYPOINT ["/custom-docker-entrypoint.sh"]
CMD ["opensearch"]
