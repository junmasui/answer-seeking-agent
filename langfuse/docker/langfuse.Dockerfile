FROM langfuse/langfuse:3.24

USER root

RUN apk update && apk --no-cache add curl postgresql-client bind-tools

COPY --from=parent-dir ./custom-web-entrypoint.sh /custom-web-entrypoint.sh

# Revert back to the configured user in the langfuse image.
#
# The user is found by running:
#   docker inspect langfuse/langfuse:3.24 | jq '.[0].Config.User'
#
USER nextjs

ENTRYPOINT ["dumb-init", "--", "/custom-web-entrypoint.sh"]

# Need to copy CMD from base image:
# See: https://docs.docker.com/reference/dockerfile/#understand-how-cmd-and-entrypoint-interact
#
# The CMD is found by running:
#   docker inspect langfuse/langfuse:3.24 | jq '.[0].Config.Cmd'
#
CMD ["node", "./web/server.js", "--keepAliveTimeout", "110000"]
