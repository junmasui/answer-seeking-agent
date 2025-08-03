To add a dependency, follow these steps:

Log into container:

```bash
docker compose --profile backend exec -it api-server bash
```

Activate the `uv` virtual environment.

```bash
/custom-docker-entrypoint.sh
```

Add the dependency

```bash
uv add --no-sync mypackage
```

Synchronize the environment to the specifications

```bash
uv sync  --extra cuda12 --dev
```
