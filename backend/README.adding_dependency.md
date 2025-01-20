To add a dependency, follow these steps:

Log into container:

```
docker compose --profile backend exec -it fastapi-dev-server bash
```

Activate the `uv` virtual environment.
```
/custom-docker-entrypoint.sh
```

Add the dependency
```
uv add --no-sync mypackage
```

Generate the requirements files

```
uv pip compile pyproject.toml --extra cuda12 -o requirements-cuda12.compiled.txt --emit-index-url
uv pip compile pyproject.toml --extra cpu -o requirements-cpu.compiled.txt --emit-index-url --index https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match --emit-index-annotation
```
