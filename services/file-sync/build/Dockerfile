FROM debian:bookworm-slim

# Install Unison, FUSE, and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    unison \
    fuse3 \
    curl \
    procps \
    supervisor \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install SeaweedFS CLI (weed)
# Using a fixed version or latest. Here fetching latest release binary.
# Note: In production, pinning version is better.
RUN curl -L https://github.com/seaweedfs/seaweedfs/releases/download/3.64/linux_amd64.tar.gz | tar xz -C /usr/local/bin weed

# Create mount point
RUN mkdir -p /mnt/fuse

# Copy scripts
COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./run_sync.sh /run_sync.sh
COPY --from=config-dir ./supervisord.conf /etc/supervisord.conf

RUN chmod +x /custom-docker-entrypoint.sh \
    && chmod +x /run_sync.sh

CMD ["/custom-docker-entrypoint.sh"]
