FROM docker.io/python:3.12.10-slim-bookworm


ARG USER_ID=1000
ARG GROUP_ID=1000

RUN \
    set -eux ; \
    \
    # Create a custom group with GROUP_ID
    # Then create a custom user with USER_ID and GROUP_ID
    #
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} python ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} python ; \
    #
    # Locally required Debian packages
    #
    apt-get update && \
    apt-get install -y \
        bind9-dnsutils \
        curl \
        libgl1 \
        libgl1-mesa-dri \
        libglu1-mesa \
        libglx-mesa0 \
        libmagic1 \
        libx11-6 \
        libxext6 \
        poppler-utils \
        tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* ; \
    #
    # Install uv package manager
    #
    pip install uv

#
# This script lives in the parent of the current directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1

COPY --from=parent-dir ./custom-docker-entrypoint.sh /
COPY --from=parent-dir ./run_celery_worker.sh /
COPY --from=parent-dir ./run_celery_flower.sh /
COPY --from=parent-dir ./run_fastapi_dev_server.sh /

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /run_celery_worker.sh \
    && chmod a+x /run_celery_flower.sh \
    && chmod a+x /run_fastapi_dev_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_worker.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_flower.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_fastapi_dev_server.sh

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

# Set the working directory inside the container
WORKDIR /app

COPY --from=parent-dir ./pyproject.toml /app/pyproject.toml

COPY --from=parent-dir ./alembic.ini /app/alembic.ini
COPY --from=parent-dir ./logging.toml /app/logging.toml
COPY --from=parent-dir ./uv.lock /app/uv.lock
COPY --from=parent-dir ./src/ /app/src/

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the FastAPI development server
CMD [ "/run_fastapi_dev_server.sh" ]
