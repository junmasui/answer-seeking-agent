# Use an official Node.js image as the base image
FROM docker.io/node:22-bookworm-slim AS production

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
COPY --from=config-dir ./custom-docker-entrypoint.sh /
COPY --from=config-dir ./run_webui_server.sh /

COPY --from=dependency-gate-dir ./wait_for_resource.sh /



## RUN chmod a+x /custom-docker-entrypoint.sh \
##     && chmod a+x /run_webui_server.sh \
##     && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
##     && chown ${USER_ID}:${GROUP_ID} /run_webui_server.sh
RUN chmod a+x /run_webui_server.sh \
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

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

RUN \
    set -eux ; \
    npm install --ignore-scripts

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the Vue.js development server
CMD ["run_webui_server.sh"]


FROM production AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# This is to allow the container user to mount the directory from the NFS server.
# The user will run the following command:
#   sudo mount /app/frontend
RUN apt-get update \
    && apt-get install -y sudo \
    && echo "nfs:/frontend /mnt/frontend-nfs nfs defaults,noauto 0 0" >> /etc/fstab \
    && echo "/mnt/frontend-nfs /app/frontend none defaults,bind,noauto 0 0" >> /etc/fstab \
    && echo "/home/node/node_modules-storage /app/frontend/node_modules none defaults,bind,noauto 0 0" >> /etc/fstab \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/mount /mnt/frontend-nfs' >> /etc/sudoers \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/umount /mnt/frontend-nfs' >> /etc/sudoers \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/mount /app/frontend' >> /etc/sudoers \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/umount /app/frontend' >> /etc/sudoers \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/mount /app/frontend/node_modules' >> /etc/sudoers \
    && echo 'node ALL=(ALL) NOPASSWD: /usr/bin/umount /app/frontend/node_modules' >> /etc/sudoers \
    && mkdir -p /mnt/frontend-nfs \
    && mkdir -p /home/node/node_modules-storage \
    && chown ${USER_ID}:${GROUP_ID} /home/node/node_modules-storage \
    && rm -rf /var/lib/apt/lists/*

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

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}
