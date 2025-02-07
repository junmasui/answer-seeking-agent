FROM langfuse/langfuse:3.24

USER root

RUN apk --no-cache add curl

# Revert back to the configured user in the langfuse image.
#
# The user is visible at
# https://hub.docker.com/layers/langfuse/langfuse/sha-2359d7f/images/sha256-6c96488b1f422748d569598cc394ab78b8839ba53739ee73f870836c0f83bf8a
#
USER nextjs
