# Docker Named Volume Initialization Experiments

This document details two experiments conducted to empirically determine the behavior of Docker named volumes during initialization, specifically focusing on data population and permission inheritance.

## Experiment 1: Volume Initialization with Restrictive Root Permissions

**Objective**: Determine if Docker populates a new named volume from the image content even if the container user lacks permissions to read the source directory, and whether the copied data retains the original restrictive permissions.

### Methodology

1.  **Dockerfile Construction**: A Docker image was created where a directory `/original` is owned by `root:root` with strictly restrictive permissions (`0700`). The image is configured to run as a non-privileged user (`testuser`, UID 1000).

    ```dockerfile
    FROM debian:bookworm-slim
    RUN mkdir /original && \
        echo "content" > /original/file && \
        chmod 700 /original && \
        chown root:root /original && \
        useradd -u 1000 testuser
    USER testuser
    ```

2.  **Execution Procedure**:
    *   Build the image `test-vol-perms`.
    *   Create a new named volume `test-vol-123`.
    *   Run the container mounting `test-vol-123` to `/original` and attempt to list the contents as the default non-privileged user.
    *   Run a second container as `root` (using the base image) to verify the actual content of the volume.

### script
```bash
# Build image
docker build -t test-vol-perms -f Dockerfile.test . 

# Create volume
docker volume create test-vol-123

# Attempt access as non-root user (Expected Failure)
docker run --rm -v test-vol-123:/original test-vol-perms ls -la /original || echo "Container user cannot read"

# Verify content as root (Expected Success)
docker run --rm -v test-vol-123:/original debian:bookworm-slim ls -la /original
```

### Results & Output

```text
test-vol-123
ls: cannot open directory '/original': Permission denied
Container user cannot read
total 12
drwx------ 2 root root 4096 Dec 27 18:02 .
drwxr-xr-x 1 root root 4096 Dec 27 18:02 ..
-rw-r--r-- 1 root root    8 Dec 27 18:02 file
```

### Interpretation

The results confirm that the Docker daemon (running as root) successfully hydrates the new volume `test-vol-123` with the data from `/original` in the image. However, the files in the volume **strictly retain the ownership (root:root) and permissions (700)** defined in the image.

Consequently, the containerized application running as `testuser` (UID 1000) was denied access (`Permission denied`), despite the data physically existing in the volume. This demonstrates that **volume population occurs independently of the container's runtime user**, but access control is enforced based on the preserved filesystem metadata. This necessitates the use of "init containers" or entrypoint scripts to fix permissions (`chown`) when the image's filesystem permissions do not align with the runtime user.

---

## Experiment 2: Volume Initialization with Custom Ownership

**Objective**: Verify if baking the correct non-root ownership into the image allows a new named volume to be immediately accessible by the non-root container user without runtime initialization steps.

### Methodology

1.  **Dockerfile Construction**: A Docker image was created where the target directory (`/data`) and its contents are explicitly owned by a non-root user (`appuser`, UID 1001) during the build process.

    ```dockerfile
    FROM debian:bookworm-slim
    RUN groupadd -g 1001 appgroup && \
        useradd -u 1001 -g appgroup appuser && \
        mkdir /data && \
        echo "pre-existing-data" > /data/file.txt && \
        chown -R appuser:appgroup /data
    USER appuser
    CMD ["ls", "-la", "/data"]
    ```

2.  **Execution Procedure**:
    *   Build the image `test-custom-perms`.
    *   Create a new named volume `test-vol-custom`.
    *   Run the container mounting `test-vol-custom` to `/data`. The default `CMD` attempts to list the directory contents.

### Script
```bash
# Build image
docker build -t test-custom-perms -f Dockerfile.custom .

# Create volume
docker volume create test-vol-custom

# Run container (Expected Success)
docker run --rm -v test-vol-custom:/data test-custom-perms
```

### Results & Output

```text
test-vol-custom
total 12
drwxr-xr-x 2 appuser appgroup 4096 Dec 27 18:04 .
drwxr-xr-x 1 root    root     4096 Dec 27 18:04 ..
-rw-r--r-- 1 appuser appgroup   18 Dec 27 18:04 file.txt
```

### Interpretation

The experiment was successful. The output `drwxr-xr-x ... appuser appgroup` confirms that when Docker populated the new volume, it preserved the `appuser:appgroup` ownership defined in the image layer. Because the container process was also running as `appuser`, it had immediate READ/WRITE access to the volume data.

This proves that **if the image's directory ownership matches the container's runtime user**, named volumes will function correctly immediately upon creation without requiring `chown` or `chmod` operations at startup. This approach allows for cleaner Compose configurations by eliminating the need for initialization containers, at the cost of requiring custom Docker images tailored to specific UIDs.
