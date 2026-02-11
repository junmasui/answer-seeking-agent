"""Constants and configuration for Dagster orchestration."""

from pathlib import Path

# Root directory of services (relative to ops/ directory)
SERVICES_ROOT = Path(__file__).resolve().parents[2] / "services"
SCRIPTS_DIR = SERVICES_ROOT / "scripts"

# Services that require custom Docker images
CUSTOM_IMAGE_DIRS = [
    "slim-util",
    "seaweedfs",
    "redis",
    "opensearch",
    "traefik",
    "weaviate",
    "api-server",
    "nemo",
    "webui-server",
    # "dev-server",
]
