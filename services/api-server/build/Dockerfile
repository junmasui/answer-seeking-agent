#
# STAGE: production
#
FROM docker.io/python:3.12.10-slim-bookworm AS production


ARG USER_ID=1000
ARG GROUP_ID=1000

RUN \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN \
    set -eux ; \
    #
    # Create a custom group with GROUP_ID
    # Then create a custom user with USER_ID and GROUP_ID and home directory.
    #
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} python ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} python ;

RUN \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    #
    # Locally required Debian packages
    #
    apt-get update \
    && apt-get install -y --no-install-recommends \
    nfs-common \
    libgl1 \
    libgl1-mesa-dri \
    libglu1-mesa \
    libglx-mesa0 \
    libx11-6 \
    libxext6 \
    #
    # Install unstructured dependencies
    #
    # See: https://docs.unstructured.io/open-source/introduction/quick-start
    #
    && apt-get install -y --no-install-recommends \
    libmagic1 \
    libreoffice \
    poppler-utils \
    tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    #
    # Install pandoc 3
    #
    # See: https://github.com/Unstructured-IO/unstructured/blob/main/scripts/install-pandoc.sh
    #
    && curl -O -sS -f --proto "=https" --proto-redir "=https" -L \
    https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-linux-amd64.tar.gz \
    && tar xvf pandoc-3.7.0.2-linux-amd64.tar.gz \
    && cd pandoc-3.7.0.2 \
    && cp bin/pandoc /usr/local/bin/ \
    && cd .. \
    && rm -rf pandoc-3.7.0* \
    #
    # Install uv package manager
    #
    && pip install --no-cache-dir uv

#
# These script live in the parent of this dockerfile's directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1

COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./run_api_server.sh /run_api_server.sh

COPY --from=celery-config-dir ./run_celery_worker.sh /run_celery_worker.sh
COPY --from=celery-config-dir ./run_celery_flower.sh /run_celery_flower.sh

COPY --from=dependency-gate-dir ./wait_for_gate.sh /
COPY --from=dependency-gate-dir ./wait_for_resource.sh /

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /run_celery_worker.sh \
    && chmod a+x /run_celery_flower.sh \
    && chmod a+x /run_api_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_worker.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_flower.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_api_server.sh \
    && mkdir /staging \
    && chown ${USER_ID}:${GROUP_ID} /staging

# Set the working directory inside the container
WORKDIR /app/backend/

COPY --from=backend-dir ./pyproject.toml /app/backend/pyproject.toml
COPY --from=backend-dir ./uv.lock /app/backend/uv.lock

COPY --from=backend-dir ./alembic.ini /app/backend/alembic.ini
COPY --from=backend-dir ./logging.toml /app/backend/logging.toml
COPY --from=backend-dir ./apps/ /app/backend/apps/
COPY --from=backend-dir ./libs/ /app/backend/libs/

RUN chown -R ${USER_ID}:${GROUP_ID} /app/

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

RUN \
    set -eux ; \
    uv venv --allow-existing \
    && uv sync --extra cpu --dev --all-packages


ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the FastAPI development server
CMD [ "/run_api_server.sh" ]

#
# STAGE: dev
#
FROM production AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

# This is to allow the container user to mount the directory from the NFS server.
# The user will run the following command:
#   sudo mount /app/backend
RUN \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y sudo \
    #
    # FSAL_VFS is the only Ganesha module for exporting standard Linux filesystem.
    # This module has a broken "Spare Read" features that failes on Docker / overlay2.
    # The NFS client is forced into 4.1 protocol which does not support the failing READ_PLUS.
    #
    && echo "nfs:/backend /mnt/backend-nfs nfs defaults,noauto,noac,nfsvers=4.1 0 0" >> /etc/fstab \
    && echo "/mnt/backend-nfs /app/backend none defaults,bind,noauto 0 0" >> /etc/fstab \
    && echo "/home/python/.venv-storage /app/backend/.venv none defaults,bind,noauto 0 0" >> /etc/fstab \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /mnt/backend-nfs' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /mnt/backend-nfs' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /app/backend' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /app/backend' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/mount /app/backend/.venv' >> /etc/sudoers \
    && echo 'python ALL=(ALL) NOPASSWD: /usr/bin/umount /app/backend/.venv' >> /etc/sudoers \
    && mkdir -p /mnt/backend-nfs \
    && mkdir -p /home/python/.venv-storage && chown ${USER_ID}:${GROUP_ID} /home/python/.venv-storage \
    && rm -rf /var/lib/apt/lists/*

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

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}
