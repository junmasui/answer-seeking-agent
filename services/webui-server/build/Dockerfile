# Use an official Node.js image as the base image
FROM docker.io/node:22-bookworm-slim AS production-base

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    # Install Debian packages
    && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    wget \
    gosu \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; \
    gosu nobody true ; \
    #
    # Create a custom group with GROUP_ID
    # Then create a custom user with USER_ID and GROUP_ID
    #
    set -eux ; \
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} node ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} node

# Copy the build-and-run script.
#
# These script live in the parent of this dockerfile's directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1
COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh
COPY --from=config-dir ./run_webui_server.sh /run_webui_server.sh
COPY --from=config-dir ./supervisord.conf /etc/supervisord.conf
COPY --from=config-dir ./webui_mount_helper.sh /usr/local/bin/webui_mount_helper.sh

COPY --from=dependency-gate-dir ./wait_for_resource.sh /



RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /custom-docker-entrypoint-nonpriv.sh \
    && chmod a+x /run_webui_server.sh \
    && chmod a+x /usr/local/bin/webui_mount_helper.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint-nonpriv.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_webui_server.sh

# Set the working directory inside the container
WORKDIR /app/frontend/

COPY --from=frontend-dir ./index.html /app/frontend/index.html
COPY --from=frontend-dir ./jsconfig.json /app/frontend/jsconfig.json
COPY --from=frontend-dir ./package-lock.json /app/frontend/package-lock.json
COPY --from=frontend-dir ./package.json /app/frontend/package.json
COPY --from=frontend-dir ./vite.config.js /app/frontend/vite.config.js

COPY --from=frontend-dir ./src/ /app/frontend/src/

RUN chown -R ${USER_ID}:${GROUP_ID} /app/frontend/

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the Vue.js development server
CMD ["run_webui_server.sh"]

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

FROM production-base AS production

ARG USER_ID=1000
ARG GROUP_ID=1000

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}


RUN \
    set -eux ; \
    npm install --ignore-scripts

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}


FROM production-base AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# This is to allow the container user to mount the directory using FUSE.
# The user will run the 'weed mount' command.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    fuse3 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    # Install weed CLI
    && curl -L https://github.com/seaweedfs/seaweedfs/releases/download/3.79/linux_amd64.tar.gz | tar xz -C /usr/local/bin weed

RUN \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    bind9-dnsutils \
    iproute2 \
    psmisc \
    tree \
    openssh-client \
    patch \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the Vue.js development server
CMD ["run_webui_server.sh"]

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}
