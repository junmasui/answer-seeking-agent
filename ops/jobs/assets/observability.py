"""Observability service assets (metrics, logs, traces)."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _start_service
from .databases import postgres_mlflow_init_service
from .images import ALL_IMAGE_ASSETS
from .infrastructure import seaweedfs_init_mlflow_service
from .scripts import update_secrets_asset


@asset(
    name="prometheus",
    required_resource_keys={"compose_env", "process_checker"},
    deps=ALL_IMAGE_ASSETS,
    retry_policy=RetryPolicy(max_retries=15),
)
def prometheus_service(context) -> Dict[str, str]:
    """Start Prometheus metrics service."""
    _start_service(context, "prometheus")
    return {"status": "ready"}
    
    
@asset(
    name="loki",
    required_resource_keys={"compose_env", "process_checker"},
    deps=ALL_IMAGE_ASSETS,
    retry_policy=RetryPolicy(max_retries=15),
)
def loki_service(context) -> Dict[str, str]:
    """Start Loki log aggregation service."""
    _start_service(context, "loki")
    return {"status": "ready"}


@asset(
    name="grafana",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[prometheus_service, loki_service, update_secrets_asset],
    retry_policy=RetryPolicy(max_retries=15),
)
def grafana_service(context) -> Dict[str, str]:
    """Start Grafana visualization service."""
    _start_service(context, "grafana")
    return {"status": "ready"}


@asset(
    name="jaeger",
    required_resource_keys={"compose_env", "process_checker"},
    deps=ALL_IMAGE_ASSETS,
    retry_policy=RetryPolicy(max_retries=15),
)
def jaeger_service(context) -> Dict[str, str]:
    """Start Jaeger tracing service."""
    _start_service(context, "jaeger")
    return {"status": "ready"}


@asset(
    name="otel-collector",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[*ALL_IMAGE_ASSETS, loki_service, jaeger_service, prometheus_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def otel_collector_service(context) -> Dict[str, str]:
    """Start OpenTelemetry collector service."""
    _start_service(context, "otel-collector")
    return {"status": "ready"}


@asset(
    name="otel-collector-docker",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[*ALL_IMAGE_ASSETS, loki_service, jaeger_service, prometheus_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def otel_collector_docker_service(context) -> Dict[str, str]:
    """Start OpenTelemetry collector for Docker metrics."""
    _start_service(context, "otel-collector-docker")
    return {"status": "ready"}


@asset(
    name="mlflow",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[postgres_mlflow_init_service, seaweedfs_init_mlflow_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def mlflow_service(context) -> Dict[str, str]:
    """Start MLflow tracking server."""
    _start_service(context, "mlflow")
    return {"status": "ready"}
