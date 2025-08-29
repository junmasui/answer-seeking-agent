FROM python:3.12-slim-bookworm


# Install gcc/g++ for annoy
RUN apt-get update && \
    apt-get install -y gcc g++

# ##ENV UV_SYSTEM_PYTHON=1

# RUN if [ "$(uname -m)" = "x86_64" ]; then \
#   export ANNOY_COMPILER_ARGS="-D_CRT_SECURE_NO_WARNINGS,-DANNOYLIB_MULTITHREADED_BUILD,-march=x86-64"; \
#   fi

# Install uv
RUN pip install --no-cache-dir uv

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Copy project files
WORKDIR /app

COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock

## RUN uv init --bare --name bare
## RUN uv add --no-sync nemoguardrails
RUN uv sync

# Download the `all-MiniLM-L6-v2` model
RUN uv run python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

RUN uv run nemoguardrails --help


# Ensure the entry point is installed as a script


# opentelemetry-instrument --logs_exporter console --metrics_exporter none --traces_exporter console

# uv run opentelemetry-instrument --logs_exporter console --traces_exporter console nemoguardrails server --verbose  --config=/config
# uv run opentelemetry-instrument --logs_exporter console --metrics_exporter none --traces_exporter console nemoguardrails server --verbose  --config=/config
# uv run opentelemetry-instrument --logs_exporter=console --metrics_exporter=none --traces_exporter=console  nemoguardrails
# uv run opentelemetry-instrument nemoguardrails server --verbose  --config=/config

ENTRYPOINT ["uv", "run", "nemoguardrails"]
CMD ["server", "--verbose", "--config=/config"]
