# Start with the Node.js image to copy artifacts from
# NOTE: This is overridden by --build-context node-source=docker-image://...
FROM node-source AS node-source

# Alias the backend base image
# NOTE: This is overridden by --build-context backend-source=docker-image://...
FROM backend-source AS backend-source

#
# STAGE: production
#
FROM backend-source AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# Copy node and its components from the official Node image.
COPY --from=node-source /usr/local/bin/node /usr/local/bin/node
COPY --from=node-source /usr/local/lib/node_modules/ /usr/local/lib/node_modules/
# Copy soft links as soft links
RUN --mount=type=bind,from=node-source,target=/context \
    cp -a /context/usr/local/bin/nodejs /usr/local/bin/nodejs \
    && cp -a /context/usr/local/bin/npm /usr/local/bin/npm \
    && cp -a /context/usr/local/bin/npx /usr/local/bin/npx \
    && cp -a /context/usr/local/bin/corepack /usr/local/bin/corepack


#
# Copy scripts
#
COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh
COPY --from=config-dir ./supervisord.conf /etc/supervisord.conf
COPY --from=config-dir ./stop_supervisor.sh /stop_supervisor.sh
COPY --from=config-dir ./dev_mount_helper.sh /usr/local/bin/dev_mount_helper.sh

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /custom-docker-entrypoint-nonpriv.sh \
    && chmod a+x /stop_supervisor.sh \
    && chmod a+x /usr/local/bin/dev_mount_helper.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint-nonpriv.sh

# Set the working directory inside the container
WORKDIR /app

RUN chown -R ${USER_ID}:${GROUP_ID} /app/

#
# Create internal storage directories for .venv and node_modules.
# These are bind-mounted over /app at runtime by dev_mount_helper.sh.
#
RUN mkdir -p /home/python/.venv-storage \
    && mkdir -p /home/python/node_modules-storage \
    && chown ${USER_ID}:${GROUP_ID} /home/python/.venv-storage \
    && chown ${USER_ID}:${GROUP_ID} /home/python/node_modules-storage

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    bind9-dnsutils \
    iproute2 \
    psmisc \
    tree \
    ca-certificates \
    openssh-client \
    sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && . /etc/os-release \
    && printf "Types: deb\nURIs: https://download.docker.com/linux/debian\nSuites: ${VERSION_CODENAME}\nComponents: stable\nSigned-By: /etc/apt/keyrings/docker.asc\n" > /etc/apt/sources.list.d/docker.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# antigravity editor needs curl git and tar
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    curl wget git procps tar patch supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Wrapper to fix buggy antigravity behavior adding extra colon.
# The extra colon is in a command that is passed to the container when installing the
# antigravity server. The logs indicate the specific command is:
# 
#   docker exec -u root <container-name> chown 1000:1000: /tmp/<randomized-name>.sh
#
RUN echo '#!/bin/bash' > /usr/local/bin/chown \
    && echo 'args=("$@")' >> /usr/local/bin/chown \
    && echo 'for ((i=0; i<${#args[@]}; i++)); do' >> /usr/local/bin/chown \
    && echo '    if [ "${args[i]}" = "1000:1000:" ]; then' >> /usr/local/bin/chown \
    && echo '        args[i]="1000:1000"' >> /usr/local/bin/chown \
    && echo '    fi' >> /usr/local/bin/chown \
    && echo 'done' >> /usr/local/bin/chown \
    && echo 'exec /usr/bin/chown "${args[@]}"' >> /usr/local/bin/chown \
    && chmod +x /usr/local/bin/chown

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Default command doing nothing, as this is a dev container
CMD [ "bash" ]
