FROM debian:12-slim

# Make package installs non-interactive in Docker builds
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    nfs-ganesha nfs-common nfs-ganesha-vfs \
 && rm -rf /var/lib/apt/lists/*

# Copy the configuration from the named build stage or image `config-dir`.
# The original build uses a sibling stage/image providing the file.
# Keep the original multi-stage copy here so CI/build scripts that provide
# `config-dir` continue to work.
COPY --from=config-dir ./ganesha.conf /etc/ganesha/ganesha.conf

# Ensure export path exists before VOLUME so it's properly baked into the layer.
# VFS FSAL needs read+execute on the directory to resolve filesystem paths.
RUN mkdir -p /exports && chmod 777 /exports && chown root:root /exports

VOLUME /exports

EXPOSE 2049/tcp 2049/udp

RUN mkdir -p /var/log && touch /var/log/ganesha.log

# Ensure runtime directory exists at build time
RUN mkdir -p /var/run/ganesha && chmod 755 /var/run/ganesha

# Copy entrypoint script for diagnostics and startup
COPY --from=config-dir ./docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Run ganesha directly. Prefer the executable from PATH so different
# distributions (where it's installed in /usr/sbin or /usr/bin) continue
# to work. Log to stdout so container logs are visible.
# For container networking, expose NFS ports and use docker port mapping.
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["-F", "-L", "/dev/stdout"]
