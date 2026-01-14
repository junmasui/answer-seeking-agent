# Use Debian 12 slim as the base image (stable)
FROM debian:bookworm-slim

# Set SeaweedFS version
ARG SEAWEED_VERSION=3.75

# Install dependencies and download SeaweedFS
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gettext-base \
    && curl -L https://github.com/seaweedfs/seaweedfs/releases/download/${SEAWEED_VERSION}/linux_amd64.tar.gz -o /tmp/seaweed.tar.gz \
    && tar -xzf /tmp/seaweed.tar.gz -C /usr/bin/ weed \
    && rm /tmp/seaweed.tar.gz \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /scripts

# Copy initialization script
COPY --from=config-dir ./init-seaweedfs.sh /init-seaweedfs.sh

# Ensure script is executable
RUN chmod +x /init-seaweedfs.sh

# Entrypoint setup
ENTRYPOINT ["/init-seaweedfs.sh"]
