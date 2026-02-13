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

## Commands

- **Start**: `docker compose --profile <profile> up -d`
- **Logs**: `docker compose logs <service>` (e.g., `minio`, `pgvector`)
- **Stop All**: `docker compose --profile all down --remove-orphans` (mirrors `services/scripts/full_stop.sh`)
- **Rebuild Images**: `./build_images.sh` (rebuilds custom CUDA/CPU images)

## Secrets

- **Location**: `secrets/` folders.
- **Rule**: Do not commit secrets. Use `.env` files in `secrets/`. Do not hardcode sensitive values.

## New Service Checklist

- [ ] **Dockerfile**: Create `apps/<service>/build/Dockerfile`.
- [ ] **Config**: Place default config in `apps/<service>/config/`.
- [ ] **Compose**: Add entry to `services/docker-compose.yaml` (or relevant split file).
- [ ] **Profile**: Assign a profile (e.g., `backend` or `infrastructure`).
- [ ] **Healthcheck**: Implement a `healthcheck` in the compose definition.
- [ ] **Logs**: Verify logs appear in `docker compose logs <service>`.
- [ ] **Networking**: Ensure it uses the `agent-poc` network to talk to other containers by service name.
- [ ] **Persistence**: Use top-level named volumes to persist data across service down-up cycles.
