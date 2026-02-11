# Dagster Operations

Host-based Dagster orchestration for the answer-seeking-agent project.

## Setup

Install dependencies using uv:

```bash
cd ops
uv sync
```

This creates an isolated virtual environment in `ops/.venv/` without polluting your host system.

Set the Dagster home directory:

```bash
export DAGSTER_HOME="$(pwd)/.dagster"
```

This tells Dagster to store its metadata, logs, and SQLite database in `ops/.dagster/`. You may want to add this to your shell configuration file (e.g., `~/.bashrc` or `~/.zshrc`) to avoid setting it each time.

## Running Dagster

### Development Server

Start the Dagster webserver and daemon:

```bash
cd ops
uv run dagster dev
```

The UI will be available at <http://localhost:3000>

### Running Jobs

The recommended way to run jobs is from the Dagster UI at <http://localhost:3000> after starting `dagster dev`.

Alternatively, you can use the CLI to execute jobs immediately (with `dagster dev` **stopped**):

```bash
cd ops
uv run dg job launch --job launch_services
```

Or using the older command:

```bash
cd ops
uv run dagster job execute -m jobs -j launch_services
```

> [!NOTE]
> The `dg` command is Dagster's newer CLI interface. Both commands execute jobs synchronously in standalone mode.

## Project Structure

```text
ops/
├── jobs/                    # Python module containing Dagster definitions
│   ├── __init__.py         # Exports main 'defs' object
│   ├── constants.py        # Path constants and configuration
│   ├── resources.py        # Dagster resources
│   ├── helpers.py          # Helper functions
│   ├── jobs.py            # Job definitions
│   └── assets/            # Asset definitions organized by domain
│       ├── __init__.py
│       ├── images.py      # Docker image building
│       ├── databases.py   # Database services
│       ├── infrastructure.py  # Redis, OpenSearch, Weaviate, SeaweedFS
│       ├── auth.py        # Keycloak authentication
│       ├── observability.py  # Prometheus, Grafana, Jaeger, Loki
│       ├── services.py    # Application services
│       ├── autotest.py    # Test environment services
│       └── scripts.py     # Script-based operations
├── pyproject.toml         # Python dependencies
├── workspace.yaml         # Dagster workspace configuration
└── .dagster/             # Dagster home (SQLite DB, logs)
```

## Environment

Dagster home is set to `ops/.dagster/` which contains:

- SQLite database for run history and asset metadata
- Logs and execution artifacts
- Scheduler state

All data stays within the `ops/` directory for easy cleanup if needed.
