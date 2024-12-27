FROM python:3.12.8-slim-bookworm

#
# https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/12.6.3/ubuntu2404/base/Dockerfile
#


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gnupg2 \
        curl \
        ca-certificates \
    && curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64/3bf863cc.pub \
        | apt-key add - \
    && echo "deb https://developer.download.nvidia.com/compute/cuda/repos/debian11/x86_64 /" > /etc/apt/sources.list.d/cuda.list \
    && rm -rf /var/lib/apt/lists/*
##    && apt-get purge --autoremove -y curl \


# For libraries in the cuda-compat-* package: https://docs.nvidia.com/cuda/eula/index.html#attachment-a

#
# Install the CUDA libraries installed in the base NVIDIA image.
#

ENV NV_CUDA_CUDART_VERSION=11.8.89-1

RUN apt-get update \
   && apt-get install -y --no-install-recommends \
      cuda-cudart-11-8=${NV_CUDA_CUDART_VERSION} \
      cuda-compat-11-8 \
   && rm -rf /var/lib/apt/lists/*

# Required for nvidia-docker v1
RUN echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf \
    && echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH=/usr/local/nvidia/bin:/usr/local/cuda/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64


# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility



# ENV NV_CUDA_DRIVERS_VERSION=565.57.01-1
# ENV NV_CUDA_TOOLKIT_VERSION=12.6.3-1


# RUN apt-get update \
#    && apt-get install -y --no-install-recommends \
#       cuda-drivers=${NV_CUDA_DRIVERS_VERSION} \
#       cuda-toolkit=${NV_CUDA_TOOLKIT_VERSION} \
#    && rm -rf /var/lib/apt/lists/*


# apt-get install cuda-toolkit=12.6.3-1 --no-install-recommends
# Reading package lists... Done
# Building dependency tree... Done
# Reading state information... Done
# The following additional packages will be installed:
#   adwaita-icon-theme at-spi2-common build-essential ca-certificates-java cuda-cccl-12-6 cuda-command-line-tools-12-6 cuda-compiler-12-6 cuda-crt-12-6 cuda-cudart-12-6 cuda-cudart-dev-12-6
#   cuda-cuobjdump-12-6 cuda-cupti-12-6 cuda-cupti-dev-12-6 cuda-cuxxfilt-12-6 cuda-documentation-12-6 cuda-driver-dev-12-6 cuda-gdb-12-6 cuda-libraries-12-6 cuda-libraries-dev-12-6
#   cuda-nsight-12-6 cuda-nsight-compute-12-6 cuda-nsight-systems-12-6 cuda-nvcc-12-6 cuda-nvdisasm-12-6 cuda-nvml-dev-12-6 cuda-nvprof-12-6 cuda-nvprune-12-6 cuda-nvrtc-12-6 cuda-nvrtc-dev-12-6
#   cuda-nvtx-12-6 cuda-nvvm-12-6 cuda-nvvp-12-6 cuda-opencl-12-6 cuda-opencl-dev-12-6 cuda-profiler-api-12-6 cuda-sanitizer-12-6 cuda-toolkit-12-6 cuda-toolkit-12-6-config-common
#   cuda-toolkit-12-config-common cuda-toolkit-config-common cuda-tools-12-6 cuda-visual-tools-12-6 default-jre default-jre-headless gds-tools-12-6 gtk-update-icon-cache java-common libasound2
#   libasound2-data libatk1.0-0 libavahi-client3 libavahi-common-data libavahi-common3 libcublas-12-6 libcublas-dev-12-6 libcufft-12-6 libcufft-dev-12-6 libcufile-12-6 libcufile-dev-12-6 libcups2
#   libcurand-12-6 libcurand-dev-12-6 libcusolver-12-6 libcusolver-dev-12-6 libcusparse-12-6 libcusparse-dev-12-6 libdbus-1-3 libdrm-amdgpu1 libdrm-common libdrm-intel1 libdrm-nouveau2
#   libdrm-radeon1 libdrm2 libegl-mesa0 libegl1 libgbm1 libgif7 libgl1 libgl1-mesa-dri libglapi-mesa libglvnd0 libglx-mesa0 libglx0 libgtk2.0-0 libgtk2.0-common libllvm15 libnpp-12-6
#   libnpp-dev-12-6 libnspr4 libnss3 libnvfatbin-12-6 libnvfatbin-dev-12-6 libnvjitlink-12-6 libnvjitlink-dev-12-6 libnvjpeg-12-6 libnvjpeg-dev-12-6 libopengl0 libpciaccess0 libpcsclite1
#   libsensors-config libsensors5 libwayland-client0 libwayland-server0 libx11-xcb1 libxcb-cursor0 libxcb-dri2-0 libxcb-dri3-0 libxcb-glx0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1
#   libxcb-present0 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-sync1 libxcb-util1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 libxcomposite1 libxcursor1 libxdamage1
#   libxfixes3 libxi6 libxinerama1 libxkbcommon-x11-0 libxkbcommon0 libxrandr2 libxshmfence1 libxtst6 libxxf86vm1 libz3-4 nsight-compute-2024.3.2 nsight-systems-2024.5.1 openjdk-17-jre
#   openjdk-17-jre-headless xkb-data

# apt-get install cuda-drivers=560.35.05-0ubuntu1 --no-install-recommends
# Reading package lists... Done
# Building dependency tree... Done
# Reading state information... Done
# The following additional packages will be installed:
#   cuda-drivers-560 dkms keyboard-configuration kmod libdbus-1-3 libdrm-amdgpu1 libdrm-common libdrm-intel1 libdrm-nouveau2 libdrm-radeon1 libdrm2 libegl-mesa0 libegl1 libepoxy0 libfontenc1
#   libgbm1 libgl1 libgl1-mesa-dri libglapi-mesa libglvnd0 libglx-mesa0 libglx0 libkmod2 libllvm15 liblocale-gettext-perl libnvidia-cfg1-560 libnvidia-common-560 libnvidia-compute-560
#   libnvidia-decode-560 libnvidia-encode-560 libnvidia-extra-560 libnvidia-fbc1-560 libnvidia-gl-560 libpciaccess0 libsensors-config libsensors5 libunwind8 libwayland-client0 libwayland-server0
#   libx11-xcb1 libxaw7 libxcb-dri2-0 libxcb-dri3-0 libxcb-glx0 libxcb-present0 libxcb-randr0 libxcb-sync1 libxcb-xfixes0 libxcvt0 libxfixes3 libxfont2 libxkbfile1 libxmu6 libxpm4 libxrandr2
#   libxshmfence1 libxxf86vm1 libz3-4 lsb-release nvidia-compute-utils-560 nvidia-dkms-560 nvidia-driver-560 nvidia-firmware-560-560.35.05 nvidia-kernel-common-560 nvidia-kernel-source-560
#   nvidia-modprobe nvidia-utils-560 udev x11-xkb-utils xkb-data xserver-common xserver-xorg-core xserver-xorg-video-nvidia-560




# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

#
# Install the CUDA libraries installed in the runtime NVIDIA image.
#
#
# See: https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/12.6.3/ubuntu2404/runtime/Dockerfile
#
ENV NV_CUDA_LIB_VERSION=11.8.0-1
ENV NV_LIBNPP_VERSION=11.8.0.86-1
ENV NV_NVTX_VERSION=11.8.86-1
ENV NV_LIBCUSPARSE_VERSION=11.7.5.86-1
ENV NV_LIBCUBLAS_VERSION=11.11.3.6-1
ENV NV_LIBNCCL_PACKAGE_VERSION=2.15.5-1+cuda11.8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        cuda-libraries-11-8=${NV_CUDA_LIB_VERSION} \
        libnpp-11-8=${NV_LIBNPP_VERSION} \
        cuda-nvtx-11-8=${NV_NVTX_VERSION} \
        libcusparse-11-8=${NV_LIBCUSPARSE_VERSION} \
        libcublas-11-8=${NV_LIBCUBLAS_VERSION} \
   && apt-mark hold libcublas-11-8 \
   && rm -rf /var/lib/apt/lists/*
#        libnccl2=${NV_LIBNCCL_PACKAGE_VERSION} \
#   && apt-mark hold libcublas-11-8 libnccl2 \


#
# Install the CUDNN libraries installed in the runtime NVIDIA image.
#
# See: https://gitlab.com/nvidia/container-images/cuda/blob/master/dist/12.6.3/ubuntu2404/runtime/cudnn/Dockerfile
#
ENV NV_CUDNN_VERSION=8.9.6.50-1+cuda11.8

RUN apt-get update \
   && apt-get install -y --no-install-recommends \
        libcudnn8=${NV_CUDNN_VERSION} \
   && apt-mark hold \
        libcudnn8 \
   && rm -rf /var/lib/apt/lists/*
