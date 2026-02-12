"""Application service assets."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _start_service
from .auth import keycloak_init_service
from .databases import postgres_init_service
from .images import (
    ALL_IMAGE_ASSETS,
    api_server_image,
    nemo_image,
    slim_util_image,
    traefik_image,
    webui_server_image,
)
from .infrastructure import (
    opensearch_service,
    redis_service,
    seaweedfs_init_service,
    weaviate_service,
)
from .observability import otel_collector_service


@asset(
    name="traefik",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[traefik_image],
    retry_policy=RetryPolicy(max_retries=15),
)
def traefik_service(context) -> Dict[str, str]:
    """Start Traefik reverse proxy service."""
    _start_service(context, "traefik")
    return {"status": "ready"}


@asset(
    name="slim-util",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[slim_util_image],
    retry_policy=RetryPolicy(max_retries=15),
)
def slim_util_service(context) -> Dict[str, str]:
    """Start slim-util service."""
    _start_service(context, "slim-util")
    return {"status": "ready"}


@asset(
    name="nemo-guardrails",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[nemo_image],
    retry_policy=RetryPolicy(max_retries=15),
)
def nemo_guardrails_service(context) -> Dict[str, str]:
    """Start NeMo Guardrails service."""
    _start_service(context, "nemo-guardrails")
    return {"status": "ready"}


@asset(
    name="presidio-analyzer",
    required_resource_keys={"compose_env", "process_checker"},
    deps=ALL_IMAGE_ASSETS,
    retry_policy=RetryPolicy(max_retries=15),
)
def presidio_analyzer_service(context) -> Dict[str, str]:
    """Start Presidio Analyzer service for PII detection."""
    _start_service(context, "presidio-analyzer")
    return {"status": "ready"}


@asset(
    name="api-server",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[
        api_server_image,
        postgres_init_service,  # DB must exist
        redis_service,
        opensearch_service,
        weaviate_service,
        seaweedfs_init_service,  # bucket must exist
        keycloak_init_service,  # realm must be configured
        otel_collector_service,
        traefik_service,
        presidio_analyzer_service,
        nemo_guardrails_service,
    ],
    retry_policy=RetryPolicy(max_retries=15),
)
def api_server_service(context) -> Dict[str, str]:
    """Start API server service."""
    _start_service(context, "api-server")
    return {"status": "ready"}


@asset(
    name="celery-worker",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[
        api_server_image,
        postgres_init_service,  # DB must exist
        redis_service,
        opensearch_service,
        weaviate_service,
        seaweedfs_init_service,  # bucket must exist
        keycloak_init_service,  # realm must be configured
        otel_collector_service,
        traefik_service,
        presidio_analyzer_service,
        nemo_guardrails_service,
    ],
    retry_policy=RetryPolicy(max_retries=15),
)
def celery_worker_service(context) -> Dict[str, str]:
    """Start Celery worker service."""
    _start_service(context, "celery-worker")
    return {"status": "ready"}


@asset(
    name="webui-server",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[webui_server_image, api_server_service, traefik_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def webui_server_service(context) -> Dict[str, str]:
    """Start Web UI server service."""
    _start_service(context, "webui-server")
    return {"status": "ready"}


@asset(
    name="dev-server",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[webui_server_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def dev_server_service(context) -> Dict[str, str]:
    """Start development server service."""
    _start_service(context, "dev-server")
    return {"status": "ready"}
