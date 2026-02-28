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

# ---------------------------------------------------------------------------
# Service groups for selective stop/start operations
# ---------------------------------------------------------------------------

# Production-like frontend and backend services
APP_PROD_SERVICES = [
    "api-server",
    "celery-worker",
    "celery-flower",
    "celery-exporter",
    "webui-server",
]

# Autotest frontend and backend services
APP_AUTOTEST_SERVICES = [
    "api-server-autotest",
    "celery-worker-autotest",
    "celery-flower-autotest",
    "webui-server-autotest",
]

# Automated test runner containers
AUTOMATED_TEST_SERVICES = [
    "automated-pytest",
    "automated-vitest",
]

# All application services (prod + autotest + automated tests)
ALL_APP_SERVICES = APP_PROD_SERVICES + APP_AUTOTEST_SERVICES + AUTOMATED_TEST_SERVICES

# Autotest and automated test services only
AUTOTEST_AND_TEST_SERVICES = APP_AUTOTEST_SERVICES + AUTOMATED_TEST_SERVICES
