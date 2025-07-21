
# syntax=docker/dockerfile:experimental

# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.10

# Install git and gcc/g++ for annoy
RUN apt-get update && apt-get install -y git gcc g++

# Set POETRY_VERSION environment variable
##ENV POETRY_VERSION=1.8.2
##ENV UV_SYSTEM_PYTHON=1

RUN if [ "$(uname -m)" = "x86_64" ]; then \
  export ANNOY_COMPILER_ARGS="-D_CRT_SECURE_NO_WARNINGS,-DANNOYLIB_MULTITHREADED_BUILD,-march=x86-64"; \
  fi

# Install uv
RUN pip install --no-cache-dir uv

# Make port 8000 available to the world outside this container
EXPOSE 8000

# We copy the example bot configurations
WORKDIR /config
COPY ./examples/bots /config


# Copy project files
WORKDIR /app

COPY . /app/
COPY --from=parent-dir ./pyproject.toml /app/
COPY --from=parent-dir ./uv.lock /app/

RUN uv lock
RUN uv sync --all-groups --all-extras

# RUN ls -1 /usr/local/lib/python3.10/site-packages
RUN ls -1 .venv/lib/python3.10/site-packages

# Download the `all-MiniLM-L6-v2` model
RUN uv run python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

RUN uv run nemoguardrails --help
# Ensure the entry point is installed as a script

ENTRYPOINT ["uv", "run", "nemoguardrails"]
CMD ["server", "--verbose", "--config=/config"]
