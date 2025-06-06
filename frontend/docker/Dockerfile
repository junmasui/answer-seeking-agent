# Use an official Node.js image as the base image
FROM docker.io/node:22-bookworm-slim

ARG USER_ID=1000
ARG GROUP_ID=1000

ENV DEBIAN_FRONTEND=noninteractive

RUN \
  apt-get update \
  # Install Debian packages
  && apt-get install -y \
     curl \
     wget \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* \
  # Create a custom group with GROUP_ID
  # Then create a custom user with USER_ID and GROUP_ID
  && set -eux ; \
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} node ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} node ;
 
# Copy the build-and-run script.
#
# These script live in the parent of this dockerfile's directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1
COPY --from=parent-dir ./custom-docker-entrypoint.sh /
COPY --from=parent-dir ./run_dev_server.sh /

COPY --from=dependency-gate-dir ./wait_for_resource.sh /



## RUN chmod a+x /custom-docker-entrypoint.sh \
##     && chmod a+x /run_dev_server.sh \
##     && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
##     && chown ${USER_ID}:${GROUP_ID} /run_dev_server.sh
RUN chmod a+x /run_dev_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_dev_server.sh

# Set the working directory inside the container
WORKDIR /app

COPY --from=parent-dir ./app/index.html /app/index.html
COPY --from=parent-dir ./app/jsconfig.json /app/jsconfig.json
COPY --from=parent-dir ./app/package-lock.json /app/package-lock.json
COPY --from=parent-dir ./app/package.json /app/package.json
COPY --from=parent-dir ./app/vite.config.js /app/vite.config.js

COPY --from=parent-dir ./app/src/ /app/src/

RUN chown -R ${USER_ID}:${GROUP_ID} /app/

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the Vue.js development server
CMD ["run_dev_server.sh"]
