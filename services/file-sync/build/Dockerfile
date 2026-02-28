# syntax=docker/dockerfile:1

FROM debian:bookworm-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    openssh-client \
    supervisor \
    ca-certificates \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CE CLI
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# Install mutagen v0.18.1
ARG MUTAGEN_VERSION=0.18.1
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then MUTAGEN_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then MUTAGEN_ARCH="arm64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -fsSL "https://github.com/mutagen-io/mutagen/releases/download/v${MUTAGEN_VERSION}/mutagen_linux_${MUTAGEN_ARCH}_v${MUTAGEN_VERSION}.tar.gz" -o /tmp/mutagen.tar.gz && \
    tar -xzf /tmp/mutagen.tar.gz -C /usr/local/bin && \
    rm /tmp/mutagen.tar.gz && \
    chmod +x /usr/local/bin/mutagen

# Create working directory
WORKDIR /app

# Copy configuration files
COPY --from=config-dir start_mutagen_sync.sh /start_mutagen_sync.sh
COPY --from=config-dir monitor_mutagen_sync.sh /monitor_mutagen_sync.sh
COPY --from=config-dir healthcheck.sh /healthcheck.sh
COPY --from=config-dir custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make scripts executable
RUN chmod +x /start_mutagen_sync.sh /monitor_mutagen_sync.sh /healthcheck.sh /custom-docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/custom-docker-entrypoint.sh"]
