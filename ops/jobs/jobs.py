"""Dagster job definitions."""

from dagster import AssetSelection, define_asset_job

from . import assets

# All service assets for the main launch job
SERVICE_ASSETS = [
    *assets.ALL_IMAGE_ASSETS,
    assets.update_secrets_asset,
    assets.postgres_service,
    assets.postgres_init_dependency_gate_service,
    assets.postgres_init_service,
    assets.postgres_keycloak_init_service,
    assets.postgres_mlflow_init_service,
    assets.postgres_init_autotest_service,
    assets.redis_service,
    assets.opensearch_service,
    assets.weaviate_service,
    assets.seaweedfs_service,
    assets.seaweedfs_init_service,
    assets.seaweedfs_init_autotest_service,
    assets.seaweedfs_init_mlflow_service,
    assets.keycloak_service,
    assets.keycloak_init_service,
    assets.prometheus_service,
    assets.grafana_service,
    assets.jaeger_service,
    assets.loki_service,
    assets.otel_collector_service,
    assets.otel_collector_docker_service,
    assets.mlflow_service,
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
]

launch_services_job = define_asset_job(
    "launch_services",
    selection=AssetSelection.assets(*SERVICE_ASSETS),
)

initialize_environment_job = define_asset_job(
    "initialize_environment",
    selection=AssetSelection.assets(*assets.ALL_IMAGE_ASSETS, assets.initialize_environment_asset),
)

build_python_packages_job = define_asset_job(
    "build_python_packages",
    selection=AssetSelection.assets(*assets.ALL_IMAGE_ASSETS, assets.build_python_packages_asset),
)
