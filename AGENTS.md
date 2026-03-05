# AGENT OPERATING GUIDE

## Project Overview & Goals

**System**: A distributed "Answer Seeking Agent" that ingests documents, processes them via ML pipelines, and serves agent through a FastAPI backend and Vue frontend.
**Goals**:

1. **Reliability**: The system must be robust, with self-healing services and comprehensive error handling.
2. **Scalability**: Services are containerized and orchestrated via Docker Compose to support horizontal scaling.
3. **Maintainability**: Code must follow strict patterns (Golden Paths) to allow multiple agents/humans to collaborate without friction.

## Output & Formatting

- **Markdown**: Always use GitHub-flavored Markdown.
- **Paths**: Always use absolute paths for file operations.
- **Conciseness**: Be concise in explanations unless asked for detail.

## Workspace overview

- `backend/` is a Python `uv` workspace that hosts the FastAPI services, workers, and shared libs. **See [backend/AGENTS.md](backend/AGENTS.md)**.
- `frontend/` is a Vue 3 + Vite SPA with ESLint-driven lint scripts. **See [frontend/AGENTS.md](frontend/AGENTS.md)**.
- `services/` contains Docker Compose definitions for the distributed stack. **See [services/AGENTS.md](services/AGENTS.md)**.
- `ops/` contains Taskfile-based orchestration for launching the service stack. **See [ops/AGENTS.md](ops/AGENTS.md)**.
- `docs/` and the various `README*.md` files explain installation heuristics.
- Secrets live in `secrets/` and are not committed; keep them out of commits and gantry.

## Dev Container & Docker Architecture

The development environment runs inside a **dev-tools** container managed by VS Code Dev Containers (see `.devcontainer/devcontainer.json`). This is **not** Docker-in-Docker. The host's Docker socket is bind-mounted into the dev container:

```
/var/run/docker.sock:/var/run/docker.sock:ro
```

All `docker` and `docker compose` CLI commands executed inside the dev container talk directly to the **host's Docker daemon**. Key consequences:

- **Bind-mount paths are resolved on the host filesystem**, not inside the dev container. The project root is at `/app` inside the container but at a different path on the host (e.g. `/home/jun/research/answer-seeking-agent`). Compose files use paths relative to their own location, and Docker Compose resolves those relative to the compose file's position on the **host** disk — this works correctly because the host and container see the same file tree via the `../../:/app` mount.
- **Never use absolute `/app/…` paths in compose volume mounts.** Relative paths (e.g. `../config/foo.yaml`) work because Compose resolves them from the compose file's host-side location. An absolute `/app/…` path would fail because `/app` does not exist on the host.
- **`docker inspect` shows host-side source paths** in mount listings (e.g. `/home/jun/research/…`), not `/app/…` paths.
- **`docker exec`** runs inside the target container's own filesystem, which is independent of both the host and the dev container.

## MCP Recommendations

- **PostgreSQL**: For inspecting `pgvector` database.
- **Docker**: For managing the microservices fleet.

## Agent workflow reminders

- **Check Sub-directory Guides**: Before working in a specific sub-directory, ALWAYS read the local `AGENTS.md` for specific rules.
- **Cite Commands**: Always cite the primary command you ran when reporting success.
- **Lockfiles**: If you change dependencies, sync the workspace with `uv sync --all-packages` (watch extras) and commit both the pyproject lockfiles and any new source files.
- **Telemetry**: If you need to add telemetry/logging coverage, verify the `core_telemetry_distro` and `core_telemetry_instrumentation` libs for existing helpers to reuse.

Use this document as the baseline for the next agent’s onboarding; update it whenever tooling changes (new lint commands, new naming rules, etc.).
