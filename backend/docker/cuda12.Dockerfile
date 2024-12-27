FROM localdomain-python:3.12.8-bookworm-cuda12-cudnn9


ARG USER_ID=1000
ARG GROUP_ID=1000

# Create a custom group with GROUP_ID
# Then create a custom user with USER_ID and GROUP_ID
RUN set -eux ; \
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} python ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} python ;
 
#
# Locally required Debian packages
#

RUN apt-get update \
    && apt-get install -y \
        curl \
        poppler-utils \
        tesseract-ocr \
        libmagic1 \
    && apt-get install -y \
        libglx-mesa0 \
        libgl1 \
        libgl1-mesa-dri \
        libglu1-mesa \
        libxext6 \
        libx11-6

#
# Install uv package manager
#
RUN pip install uv

#
# This script lives in the parent of the current directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1

COPY ./custom-docker-entrypoint.sh /
COPY --from=parent-dir ./run_celery_worker.sh /
COPY --from=parent-dir ./run_fastapi_dev_server.sh /

RUN chmod a+x /custom-docker-entrypoint.sh \
    && chmod a+x /run_celery_worker.sh \
    && chmod a+x /run_fastapi_dev_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /custom-docker-entrypoint.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_celery_worker.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_fastapi_dev_server.sh

RUN ls -l /

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

# Set the working directory inside the container
WORKDIR /app

ENTRYPOINT [ "bash", "/custom-docker-entrypoint.sh" ]

# Build the app then start the Vue.js development server
CMD ["run_fastapi_dev_server.sh"]
