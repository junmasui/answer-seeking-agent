FROM langfuse/langfuse:3.24

USER root

RUN apk update && apk --no-cache add curl postgresql-client bind-tools

# Revert back to the configured user in the langfuse image.
#
# The user is found by running:
#   docker inspect langfuse/langfuse:3.24 | jq '.[0].Config.User'
#
USER nextjs
