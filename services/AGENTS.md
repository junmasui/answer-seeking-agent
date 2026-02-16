# Services & Orchestration Agent Operating Guide

## Docker Compose Profiles

- **infrastructure**: Databases/Storage (Postgres, MinIO, Redis).
  - `docker compose --profile infrastructure up -d`
- **backend**: API Server, Worker.
  - `docker compose --profile backend up -d`
- **frontend**: Web UI.
  - `docker compose --profile frontend up -d`
- **init-volumes**: Volume preparation.
  - `docker compose --profile init-volumes up -d` (Run before depending services if volumes are fresh)

## Docker Context

> [!IMPORTANT]
> All `docker compose` commands **MUST** be executed from the `services/` directory.

The orchestration setup uses `services/common.compose.yml` which includes individual service configurations. Many of these configurations (located in `services/<service>/deploy/`) depend on shared resources defined in:

- [components.compose.yml](file:///home/jun/research/answer-seeking-agent/services/components.compose.yml): Defines common networks and secrets.

If you run `docker compose` from within a `deploy` directory, it will fail to resolve these shared components and relative paths for secrets.

### Compose Files

The `COMPOSE_FILE` environment variable **MUST** be set to include both the common configuration and the hardware-specific override:

- **GPU (CUDA)**: `export COMPOSE_FILE=common.compose.yml:cuda.compose.yml`
- **CPU Only**: `export COMPOSE_FILE=common.compose.yml:cpu-only.compose.yml`

## Commands

- **Start**: `cd services && docker compose --profile <profile> up -d`
- **Logs**: `docker compose logs <service>`
- **Stop All**: `docker compose --profile all down --remove-orphans`
- **Rebuild Images**: `./build_images.sh`

## Secrets

- **Location**: `secrets/` folders.
- **Rule**: Do not commit secrets. Use `.env` files in `secrets/`. Do not hardcode sensitive values.

## New Service Checklist

- [ ] **Dockerfile**: Create `apps/<service>/build/Dockerfile`.
- [ ] **Build Script**: Create `apps/<service>/build/build_images.sh` and add to `services/scripts/build_images.sh`.
- [ ] **Asset**: Add image build asset to `ops/jobs/assets/images.py`.

- [ ] **Config**: Place default config in `apps/<service>/config/`.
- [ ] **Compose**: Add entry to `services/docker-compose.yaml` (or relevant split file).
- [ ] **Profile**: Assign a profile (e.g., `backend` or `infrastructure`).
- [ ] **Healthcheck**: Implement a `healthcheck` in the compose definition.
- [ ] **Logs**: Verify logs appear in `docker compose logs <service>`.
- [ ] **Networking**: Ensure it uses the `agent-poc` network to talk to other containers by service name.
- [ ] **Persistence**: Use top-level named volumes to persist data across service down-up cycles.
