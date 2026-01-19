---
trigger: always_on
---

# Orchestation - Structure

Each service will have its own directory.

The subdirectory will have 3 subdirectories:

- `build`: contains Dockerfiles and are the context directory for building images.
- `config`: which have configuration and script files that are COPY'ed during builds and are bind-mounted when running.
- `deploy`: contains compose.yml and .env files for running compose services.

Additionally, there 2 non-service directories:

- `secrets`: Stores secrets without checking
- `scripts`: Contains operational scripts

