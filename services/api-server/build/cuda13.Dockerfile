FROM docker.io/python:3.12.10-slim-bookworm AS python3.12-cuda13-cudnn9

ARG USER_ID=1000
ARG GROUP_ID=1000


#
# https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/13.1.1/ubuntu2404/base/Dockerfile
#


RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    gosu \
    supervisor \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* ; \
    gosu nobody true ; \
    #
    # Create a custom group with GROUP_ID
    # Then create a custom user with USER_ID and GROUP_ID and home directory.
    #
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} python ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} python ;




# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a

#
# Install the CUDA libraries installed in the base NVIDIA image.
#

ENV NV_CUDA_CUDART_VERSION=13.1.80-1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    curl -sS -f --proto "=https" --proto-redir "=https" -L \
    https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/3bf863cc.pub \
    | apt-key add - ; \
    echo "deb https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64 /" > /etc/apt/sources.list.d/cuda.list ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    cuda-compat-13-1 \
    cuda-cudart-13-1=${NV_CUDA_CUDART_VERSION} \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Required for nvidia-docker v1
RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf \
    && echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64


# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility


#
# Install the CUDA libraries installed in the runtime NVIDIA image.
#
#
# See: https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/13.1.1/ubuntu2404/runtime/Dockerfile
#
ENV NV_CUDA_LIB_VERSION=13.1.1-1
ENV NV_LIBNPP_VERSION=13.0.3.3-1
ENV NV_NVTX_VERSION=13.1.115-1
ENV NV_LIBCUSPARSE_VERSION=12.7.3.1-1
ENV NV_LIBCUBLAS_VERSION=13.2.1.1-1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    cuda-libraries-13-1=${NV_CUDA_LIB_VERSION} \
    cuda-nvtx-13-1=${NV_NVTX_VERSION} \
    libcublas-13-1=${NV_LIBCUBLAS_VERSION} \
    libcusparse-13-1=${NV_LIBCUSPARSE_VERSION} \
    libnpp-13-1=${NV_LIBNPP_VERSION} \
    && apt-get clean \
    && apt-mark hold libcublas-13-1 \
    && rm -rf /var/lib/apt/lists/*


#
# Install the CUDNN libraries installed in the runtime NVIDIA image.
#
# See: https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/13.1.1/ubuntu2404/runtime/cudnn/Dockerfile
#
ENV NV_CUDNN_VERSION=9.17.1.4-1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    libcudnn9-cuda-13=${NV_CUDNN_VERSION} \
    && apt-get clean \
    && apt-mark hold \
    libcudnn9-cuda-13 \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    set -eux ; \
    #
    # Install uv package manager
    #
    pip install uv


#
# STAGE: production-base
#
FROM python3.12-cuda13-cudnn9 AS python3.12-cuda13-cudnn9-heavy

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    #
    # Locally required Debian packages
    #
    apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
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
    && rm -rf pandoc-3.7.0*

FROM python3.12-cuda13-cudnn9-heavy AS production-base

ARG USER_ID=1000
ARG GROUP_ID=1000

#
# These script live in the parent of this dockerfile's directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1

COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./custom-docker-entrypoint-nonpriv.sh /custom-docker-entrypoint-nonpriv.sh
COPY --from=config-dir ./run_api_server.sh /run_api_server.sh
COPY --from=config-dir ./supervisord.conf /etc/supervisord.conf

COPY --from=config-dir ./mount_helper.sh /usr/local/bin/mount_helper.sh
COPY --from=config-dir ./stop_supervisor.sh /stop_supervisor.sh

COPY --from=celery-config-dir ./run_celery_worker.sh /
COPY --from=celery-config-dir ./run_celery_flower.sh /

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /custom-docker-entrypoint-nonpriv.sh \
    && chmod a+x /run_celery_worker.sh \
    && chmod a+x /run_celery_flower.sh \
    && chmod a+x /run_api_server.sh \
    && chmod a+x /usr/local/bin/mount_helper.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint-nonpriv.sh \
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

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]


#
# STAGE: production
#
FROM production-base AS production

ARG USER_ID=1000
ARG GROUP_ID=1000

USER ${USER_ID}:${GROUP_ID}

RUN set -eux ; \
    uv venv --allow-existing \
    && uv sync --extra cuda13 --dev --all-packages --no-editable

# Build start the server
CMD ["/run_api_server.sh"]

#
# STAGE: dev
#
FROM production-base AS dev

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux ; \
    export DEBIAN_FRONTEND=noninteractive ; \
    apt-get update \
    && apt-get install -y --no-install-recommends \
    fuse3 \
    bind9-dnsutils \
    iproute2 \
    psmisc \
    tree \
    ca-certificates \
    openssh-client \
    patch \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Install weed CLI
    && curl -L https://github.com/seaweedfs/seaweedfs/releases/download/3.64/linux_amd64.tar.gz | tar xz -C /usr/local/bin weed

RUN mkdir -p /home/python/.venv-storage && chown ${USER_ID}:${GROUP_ID} /home/python/.venv-storage

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

# Build the app then start the server
CMD ["/run_api_server.sh"]
