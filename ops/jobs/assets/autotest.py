"""Autotest environment service assets."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _run_init_container, _start_service
from .auth import keycloak_init_service
from .databases import postgres_init_autotest_service
from .infrastructure import (
    redis_service,
    seaweedfs_init_autotest_service,
    weaviate_service,
)
from .observability import otel_collector_service
from .services import (
    nemo_guardrails_service,
    presidio_analyzer_service,
    traefik_service,
)


@asset(
    name="backend-autotest-dependency-gate",
    required_resource_keys={"compose_env"},
    deps=[
        postgres_init_autotest_service,
        seaweedfs_init_autotest_service,
        redis_service,
        weaviate_service,
    ],
    retry_policy=RetryPolicy(max_retries=15),
)
def backend_autotest_dependency_gate_service(context) -> Dict[str, str]:
    """Wait for autotest dependencies to be ready."""
    _run_init_container(context, "backend-autotest-dependency-gate")
    return {"status": "completed"}


@asset(
    name="api-server-autotest",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[
        backend_autotest_dependency_gate_service,
        keycloak_init_service,
        otel_collector_service,
        traefik_service,
        presidio_analyzer_service,
        nemo_guardrails_service,
    ],
    retry_policy=RetryPolicy(max_retries=15),
)
def api_server_autotest_service(context) -> Dict[str, str]:
    """Start API server autotest service."""
    _start_service(context, "api-server-autotest")
    return {"status": "ready"}


@asset(
    name="celery-worker-autotest",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[
        backend_autotest_dependency_gate_service,
        keycloak_init_service,
        otel_collector_service,
        traefik_service,
        presidio_analyzer_service,
        nemo_guardrails_service,
    ],
    retry_policy=RetryPolicy(max_retries=15),
)
def celery_worker_autotest_service(context) -> Dict[str, str]:
    """Start Celery worker autotest service."""
    _start_service(context, "celery-worker-autotest")
    return {"status": "ready"}


@asset(
    name="webui-server-autotest",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[api_server_autotest_service, traefik_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def webui_server_autotest_service(context) -> Dict[str, str]:
    """Start Web UI server autotest service."""
    _start_service(context, "webui-server-autotest")
    return {"status": "ready"}
