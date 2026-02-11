"""Authentication service assets."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _run_init_container, _start_service
from .databases import postgres_keycloak_init_service


@asset(
    name="keycloak",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[postgres_keycloak_init_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def keycloak_service(context) -> Dict[str, str]:
    """Start Keycloak authentication service."""
    _start_service(context, "keycloak")
    return {"status": "ready"}


@asset(
    name="keycloak-init",
    required_resource_keys={"compose_env"},
    deps=[keycloak_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def keycloak_init_service(context) -> Dict[str, str]:
    """Initialize Keycloak realm configuration."""
    _run_init_container(context, "keycloak-init")
    return {"status": "completed"}
