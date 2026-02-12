"""Database service assets."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _run_init_container, _start_service
from .images import ALL_IMAGE_ASSETS


@asset(
    name="postgres",
    required_resource_keys={"compose_env", "process_checker"},
    deps=ALL_IMAGE_ASSETS,
    retry_policy=RetryPolicy(max_retries=15),
)
def postgres_service(context) -> Dict[str, str]:
    """Start PostgreSQL database service."""
    _start_service(context, "postgres")
    return {"status": "ready"}


@asset(
    name="postgres-init-dependency-gate",
    required_resource_keys={"compose_env"},
    deps=[postgres_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def postgres_init_dependency_gate_service(context) -> Dict[str, str]:
    """Wait for postgres to be ready before running init containers."""
    _run_init_container(context, "postgres-init-dependency-gate")
    return {"status": "completed"}


@asset(
    name="postgres-init",
    required_resource_keys={"compose_env"},
    deps=[postgres_init_dependency_gate_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def postgres_init_service(context) -> Dict[str, str]:
    """Initialize main PostgreSQL database."""
    _run_init_container(context, "postgres-init")
    return {"status": "completed"}


@asset(
    name="postgres-keycloak-init",
    required_resource_keys={"compose_env"},
    deps=[postgres_init_dependency_gate_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def postgres_keycloak_init_service(context) -> Dict[str, str]:
    """Initialize Keycloak PostgreSQL database."""
    _run_init_container(context, "postgres-keycloak-init")
    return {"status": "completed"}


@asset(
    name="postgres-init-autotest",
    required_resource_keys={"compose_env"},
    deps=[postgres_init_dependency_gate_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def postgres_init_autotest_service(context) -> Dict[str, str]:
    """Initialize autotest PostgreSQL database."""
    _run_init_container(context, "postgres-init-autotest")
    return {"status": "completed"}
