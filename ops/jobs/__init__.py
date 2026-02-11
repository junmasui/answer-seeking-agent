"""Dagster definitions for service orchestration."""

from dagster import Definitions

from . import assets
from .jobs import build_python_packages_job, initialize_environment_job, launch_services_job
from .resources import compose_env_resource, process_checker_resource

# Collect all assets
ALL_ASSETS = [
    # Service assets
    *assets.ALL_IMAGE_ASSETS,
    assets.postgres_service,
    assets.postgres_init_dependency_gate_service,
    assets.postgres_init_service,
    assets.postgres_keycloak_init_service,
    assets.postgres_init_autotest_service,
    assets.redis_service,
    assets.opensearch_service,
    assets.weaviate_service,
    assets.seaweedfs_service,
    assets.seaweedfs_init_service,
    assets.seaweedfs_init_autotest_service,
    assets.keycloak_service,
    assets.keycloak_init_service,
    assets.prometheus_service,
    assets.grafana_service,
    assets.jaeger_service,
    assets.loki_service,
    assets.otel_collector_service,
    assets.otel_collector_docker_service,
    assets.traefik_service,
    assets.slim_util_service,
    assets.api_server_service,
    assets.celery_worker_service,
    assets.nemo_guardrails_service,
    assets.presidio_analyzer_service,
    assets.webui_server_service,
    assets.backend_autotest_dependency_gate_service,
    assets.api_server_autotest_service,
    assets.celery_worker_autotest_service,
    assets.webui_server_autotest_service,
    assets.dev_server_service,
    # Script-based assets
    assets.initialize_environment_asset,
]

# Main Dagster definitions object
defs = Definitions(
    assets=ALL_ASSETS,
    jobs=[launch_services_job, initialize_environment_job, build_python_packages_job],
    resources={
        "compose_env": compose_env_resource,
        "process_checker": process_checker_resource,
    },
)
