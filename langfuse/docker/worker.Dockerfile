FROM langfuse/langfuse-worker:3.24

USER root

RUN apk --no-cache add curl

# Revert back to the configured user in the langfuse image.
#
# The user is visible at
# https://hub.docker.com/layers/langfuse/langfuse-worker/3.24/images/sha256-cbde690def3dc942a62f5d7fc45a53bd462a980602fa3275647070d11c90d6eb
#
USER expressjs
