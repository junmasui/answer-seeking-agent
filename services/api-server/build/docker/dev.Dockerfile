FROM localhost/localhost/answers-backend:python-3.12-cpu

ARG USER_ID=1000
ARG GROUP_ID=1000

USER root

RUN \
    apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
        gnupg \
        openssh-client \
        patch \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to the custom user
USER ${USER_ID}:${GROUP_ID}
