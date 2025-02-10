FROM langfuse/langfuse-worker:3.24

USER root

RUN apk update && apk --no-cache add curl

COPY --from=parent-dir ./custom-worker-entrypoint.sh /custom-worker-entrypoint.sh

# Revert back to the configured user in the langfuse image.
#
# The user is found by running:
#   docker inspect langfuse/langfuse-worker:3.24 | jq '.[0].Config.User'
#
USER expressjs

ENTRYPOINT ["dumb-init", "--", "/custom-worker-entrypoint.sh"]

# Need to copy CMD from base image:
# See: https://docs.docker.com/reference/dockerfile/#understand-how-cmd-and-entrypoint-interact
#
# The CMD is found by running:
#   docker inspect langfuse/langfuse-worker:3.24 | jq '.[0].Config.Cmd'
#
CMD ["node", "worker/dist/index.js"]
