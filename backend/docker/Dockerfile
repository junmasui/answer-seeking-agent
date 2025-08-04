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
    apt-get update \
    && apt-get install -y --no-install-recommends \
        bind9-dnsutils \
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
    && curl -L -O --proto "=https" \
        https://github.com/jgm/pandoc/releases/download/3.7.0.2/pandoc-3.7.0.2-linux-amd64.tar.gz \
    && tar xvf pandoc-3.7.0.2-linux-amd64.tar.gz \
    && cd pandoc-3.7.0.2 \
    && cp bin/pandoc /usr/local/bin/ \
    && cd .. \
    && rm -rf pandoc-3.7.0* \
    #
    # Install uv package manager
    #
    && pip install uv

#
# These script live in the parent of this dockerfile's directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1

COPY --from=parent-dir ./custom-docker-entrypoint.sh /
COPY --from=parent-dir ./run_celery_worker.sh /
COPY --from=parent-dir ./run_celery_flower.sh /
COPY --from=parent-dir ./run_api_server.sh /

COPY --from=dependency-gate-dir ./wait_for_gate.sh /
COPY --from=dependency-gate-dir ./wait_for_resource.sh /

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /run_celery_worker.sh \
    && chmod a+x /run_celery_flower.sh \
    && chmod a+x /run_api_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_worker.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_flower.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_api_server.sh

# Set the working directory inside the container
WORKDIR /app

COPY --from=parent-dir ./pyproject.toml /app/pyproject.toml

COPY --from=parent-dir ./alembic.ini /app/alembic.ini
COPY --from=parent-dir ./logging.toml /app/logging.toml
COPY --from=parent-dir ./uv.lock /app/uv.lock
COPY --from=parent-dir ./src/ /app/src/

RUN chown -R ${USER_ID}:${GROUP_ID} /app/

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the FastAPI development server
CMD [ "/run_api_server.sh" ]
