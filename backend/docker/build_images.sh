#
# Build a general image that is based on the official Python 3.12 on Debian 12 (Bookworm)
# with CUDA 12 and CUDNN 9 installed.
#

docker buildx build \
  --file python_bookworm_cuda12.Dockerfile \
  --no-cache \
  --tag localdomain-python:3.12.8-bookworm-cuda12-cudnn9 \
  --progress=plain \
  . 2>&1 \
| tee build-python-bookworm-cuda12-cudnn9.log

# #
# # Build a general image that is based on the official Python 3.12 on Debian 12 (Bookworm)
# # with CUDA 11 and CUDNN 8 installed.
# #

# docker buildx build \
#   --file python_bookworm_cuda11.Dockerfile \
#   --no-cache \
#   --tag localdomain-python:3.12.8-bookworm-cuda11-cudnn8 \
#   --progress=plain \
#   . 2>&1 \
# | tee build-python-bookworm-cuda11-cudnn8.log

#
# Build a backend image with Python 3.12 on Debian 12
#
docker buildx build \
  --file Dockerfile \
  --build-context parent-dir=.. \
  --no-cache \
  --tag localdomain-backend:python-3.12-cpu \
  --progress=plain \
  . 2>&1 \
| tee build-backend-python-cpu.log

#
# Build a backend image with Python 3.12 on Debian 12 with CUDA 12
#
docker buildx build \
  --file cuda12.Dockerfile \
  --build-context parent-dir=.. \
  --tag localdomain-backend:python-3.12-cuda12 \
  --progress=plain \
  . 2>&1 \
| tee build-backend-python-cuda12.log

##   --no-cache \
