FROM python:3.12-slim-bookworm


# Install gcc/g++ for annoy
RUN apt-get update && \
    apt-get --no-install-recommends install -y gcc g++

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

COPY --from=config-dir ./custom-docker-entrypoint.sh /custom-docker-entrypoint.sh
COPY --from=config-dir ./pyproject.toml ./pyproject.toml
COPY --from=config-dir ./uv.lock ./uv.lock
COPY --from=config-dir ./config/  /config/

RUN uv sync

# Download the `all-MiniLM-L6-v2` model
RUN uv run python -c "from fastembed.embedding import FlagEmbedding; FlagEmbedding('sentence-transformers/all-MiniLM-L6-v2');"

RUN uv run nemoguardrails --help

## ENTRYPOINT ["uv", "run", "nemoguardrails"]
ENTRYPOINT ["bash", "/custom-docker-entrypoint.sh"]
CMD ["server", "--config=/config"]
