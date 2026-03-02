# Ops — Taskfile Orchestration

Task-based orchestration for the answer-seeking-agent service stack, powered by [Task](https://taskfile.dev/).

## Prerequisites

Install the `task` CLI: <https://taskfile.dev/installation/>

```bash
# Linux (recommended)
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

# macOS
brew install go-task
```

The helper scripts require `jq` for JSON parsing:

```bash
# Debian/Ubuntu
sudo apt-get install jq

# macOS
brew install jq
```

## Quick Start

```bash
cd ops

# Launch the full stack
task launch

# Tear down everything
task teardown

# List all available tasks
task --list
```

## Running Individual Services

Every service is a standalone task. Dependencies are resolved automatically:

```bash
# Start just PostgreSQL (builds images + runs secrets first)
task postgres

# Start the API server (starts all transitive dependencies)
task api-server

# Build all Docker images without starting services
task images
```

## Teardown

```bash
# Stop everything, remove containers and orphans
task teardown

# Stop only app services (prod + autotest + automated tests)
task teardown:app

# Stop only autotest services
task teardown:autotest
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GPU_MODE` | `cuda12` | GPU mode: `cuda12` or `cpu-only` |
| `COMPOSE_FILE` | *(auto)* | Override the compose file list |

These can be set in your shell or passed inline:

```bash
GPU_MODE=cpu-only task launch
```

## Idempotency

All service tasks include `status:` checks. If a service is already running and healthy, it is skipped. Init containers that already exited with code 0 are also skipped. To force a restart, tear down first:

```bash
task teardown && task launch
```

## Project Structure

```text
ops/
├── Taskfile.yml              # Task definitions and dependency graph
├── scripts/                  # Helper shell scripts
│   ├── compose-env.sh        # Shared env setup (COMPOSE_FILE, GPU_MODE, SERVICES_ROOT)
│   ├── wait-healthy.sh       # Start long-running service + health-check polling
│   ├── run-init-container.sh # Run one-shot init container idempotently
│   ├── build-image.sh        # Build a custom Docker image
│   ├── stop-services.sh      # Stop and remove services
│   ├── is-service-running.sh # Status check: is service running and healthy?
│   └── is-init-done.sh       # Status check: did init container exit 0?
└── README.md
```

## Dependency Graph Overview

```text
images:group1  (slim-util, seaweedfs, redis, opensearch, traefik, weaviate, api-server, mlflow, file-sync)
    │
    ├── build-python-packages
    │       ├── image:nemo
    │       └── presidio-analyzer
    │
    └── images  (= group1 + nemo + webui-server)

update-secrets ─────────────────────────────────────┐
                                                    │
postgres ── postgres-init-dependency-gate ──┬── postgres-init ──────────── api-server / celery-worker
                                           ├── postgres-keycloak-init ── keycloak ── keycloak-init ─┤
                                           ├── postgres-mlflow-init ──── mlflow                     │
                                           └── postgres-init-autotest ── backend-autotest-dep-gate  │
                                                                                                    │
redis ──────────────────────────────────────────────────────────────────────────────────────────────┤
opensearch ─────────────────────────────────────────────────────────────────────────────────────────┤
weaviate ───────────────────────────────────────────────────────────────────────────────────────────┤
seaweedfs ── seaweedfs-init ────────────────────────────────────────────────────────────────────────┤
                                                                                                    │
prometheus ─┬── grafana                                                                             │
loki ───────┤                                                                                       │
jaeger ─────┴── otel-collector ─────────────────────────────────────────────────────────────────────┤
                                                                                                    │
traefik ────────────────────────────────────────────────────────────────────────────────────────────┤
nemo-guardrails ────────────────────────────────────────────────────────────────────────────────────┤
presidio-analyzer ──────────────────────────────────────────────────────────────────────────────────┘
                                                                                                    │
                                                                            api-server ── webui-server
                                                                            celery-worker
```
