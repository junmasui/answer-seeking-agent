FROM node:20-alpine3.20 AS alpine

RUN apk update \
    && apk upgrade --no-cache curl postgresql16-client redis bind-tools

FROM langfuse/langfuse:3.24

USER root


COPY --from=alpine /usr/bin/curl /usr/bin/curl
COPY --from=alpine /usr/bin/dig /usr/bin/dig
COPY --from=alpine /usr/bin/nslookup /usr/bin/nslookup
COPY --from=alpine /usr/bin/redis-cli /usr/bin/redis-cli
COPY --from=alpine /usr/libexec/postgresql/psql /usr/libexec/postgresql/psql

RUN ln -s /usr/libexec/postgresql/psql /usr/bin/psql

# Revert back to the configured user in the langfuse image.
#
# The user is found by running:
#   docker inspect langfuse/langfuse:3.24 | jq '.[0].Config.User'
#
USER nextjs
