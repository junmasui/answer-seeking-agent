# Use an official Node.js image as the base image
FROM node:22-bookworm-slim

ARG USER_ID=1000
ARG GROUP_ID=1000

# Install Debian packages
RUN apt-get update \
  && apt-get install -y \
     curl wget


# Create a custom group with GROUP_ID
# Then create a custom user with USER_ID and GROUP_ID
RUN set -eux ; \
    ( id -g ${GROUP_ID} > /dev/null 2>&1 ) || groupadd -g ${GROUP_ID} node ; \
    ( id -u ${USER_ID} > /dev/null 2>&1 ) || useradd -m -u ${USER_ID} -g ${GROUP_ID} node ;
 
# Copy the build-and-run script.
#
# This script lives in the parent of the current directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1
COPY --from=parent-dir run_dev_server.sh /

RUN chmod +x /run_dev_server.sh \
    && chown ${USER_ID}:${GROUP_ID} /run_dev_server.sh

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}

# Set the working directory inside the container
WORKDIR /app

# Build the app then start the Vue.js development server
CMD ["run_dev_server.sh"]
