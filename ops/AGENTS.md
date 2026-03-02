# Ops / Taskfile Agent Operating Guide

## Tooling

- **Task runner**: [Task](https://taskfile.dev/) (`task` CLI). All orchestration is in `Taskfile.yml`.
- **Shell scripts**: Helper scripts live in `ops/scripts/`. They are called by Taskfile tasks and must remain independently runnable.
- **No Python dependencies**: This directory has no `pyproject.toml` or virtual environment. All logic is declarative YAML + bash.

## Commands

- `task launch`: Launch the full service stack.
- `task teardown`: Stop all services.
- `task --list`: List all available tasks.
- `task <service>`: Start a single service (dependencies resolved automatically).

## Code Style & Conventions

- **Taskfile**: Keep tasks declarative. No inline shell logic beyond a single `cmd:` line calling a script.
- **Shell scripts**: Use `set -euo pipefail`. Source `compose-env.sh` for shared environment.
- **Naming**: Task names use kebab-case matching the Docker Compose service name. Namespaced tasks use `:` (e.g., `image:redis`, `teardown:app`).

## Adding a New Service

1. If the service needs a custom image, add an `image:<name>` task in the **IMAGE BUILDS** section of `Taskfile.yml`.
2. Add a task for the service with appropriate `deps:`, `cmd:`, and `status:` fields.
3. Wire it into the `launch` task's `deps:` list (or into another service that depends on it).
4. For init containers, use `run-init-container.sh` + `is-init-done.sh`. For long-running services, use `wait-healthy.sh` + `is-service-running.sh`.

## Script Inventory

| Script | Purpose |
|---|---|
| `compose-env.sh` | Sets `SERVICES_ROOT`, `GPU_MODE`, `COMPOSE_FILE`. Sourced by all other scripts. |
| `wait-healthy.sh` | Starts a service, polls health-check, exits 0 when healthy. |
| `run-init-container.sh` | Runs a one-shot init container, waits for exit 0. |
| `build-image.sh` | Builds a custom Docker image from `services/<dir>/build/`. |
| `stop-services.sh` | Stops and removes services. `--all` for full teardown. |
| `is-service-running.sh` | Status check for `Taskfile.yml` — exits 0 if service is running+healthy. |
| `is-init-done.sh` | Status check for `Taskfile.yml` — exits 0 if init container exited 0. |

## Testing

There are no unit tests for the orchestration layer. Validation is done by running `task launch` against the live Docker environment.

