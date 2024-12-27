FROM minio/minio:RELEASE.2024-12-13T22-19-12Z-cpuv1

# This script lives in the parent of the current directory, so we must define
# the parent as a named build-context on the command line.
#
# Copy in Dockerfile has a slightly different syntax. When copying a file to
# a directory, the destination must end with a trailing slash.
# See: https://docs.docker.com/reference/dockerfile/#destination-1
COPY --from=parent-dir init-minio.sh /
RUN chmod +x /init-minio.sh
