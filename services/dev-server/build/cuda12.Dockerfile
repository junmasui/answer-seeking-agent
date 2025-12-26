# Start with the Node.js image to copy artifacts from
FROM localhost/localhost/answers-frontend:node-22-bookworm AS node-source

#
# STAGE: dev
#
FROM localhost/localhost/answers-backend:python-3.12-cuda12 AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# Copy node and its components from the official Node image.
COPY --from=node-source /usr/local/bin/node /usr/local/bin/node
COPY --from=node-source /usr/local/lib/node_modules/ /usr/local/lib/node_modules/
COPY --from=node-source /usr/local/bin/npm /usr/local/bin/npm
COPY --from=node-source /usr/local/bin/npx /usr/local/bin/npx
COPY --from=node-source /usr/local/bin/corepack /usr/local/bin/corepack


#
# Copy scripts
#
COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh

# Set the working directory inside the container
WORKDIR /app

RUN chown -R ${USER_ID}:${GROUP_ID} /app/

#
# Configure NFS and Bind Mounts
#
RUN \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y sudo \
    && echo "nfs:/exports /mnt/data nfs defaults,noauto,nfsvers=4 0 0" >> /etc/fstab \
    && echo "/mnt/data /app none defaults,bind,noauto 0 0" >> /etc/fstab \
    # Bind mount .venv and node_modules from user home to /app subdirectories
    && echo "/home/python/.venv-storage /app/backend/.venv none defaults,bind,noauto 0 0" >> /etc/fstab \
    && echo "/home/python/node_modules-storage /app/frontend/node_modules none defaults,bind,noauto 0 0" >> /etc/fstab \
    # Sudoers configuration for mounting
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /mnt/data' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /mnt/data' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /app' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /app' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /app/backend/.venv' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /app/backend/.venv' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /app/frontend/node_modules' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /app/frontend/node_modules' >> /etc/sudoers \
    && mkdir -p /mnt/data \
    && mkdir -p /home/python/.venv-storage && chown ${USER_ID}:${GROUP_ID} /home/python/.venv-storage \
    && mkdir -p /home/python/node_modules-storage && chown ${USER_ID}:${GROUP_ID} /home/python/node_modules-storage

RUN \
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
    patch \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# antigravity editor needs curl git and tar
RUN \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    curl wget git procps tar patch  \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Default command
CMD [ "bash" ]
