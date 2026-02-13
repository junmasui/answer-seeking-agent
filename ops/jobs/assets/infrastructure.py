"""Infrastructure service assets (caches, search, storage)."""

from typing import Dict

from dagster import RetryPolicy, asset

from ..helpers import _run_init_container, _start_service
from .images import opensearch_image, redis_image, seaweedfs_image, weaviate_image
from .scripts import update_secrets_asset


@asset(
    name="redis",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[redis_image, update_secrets_asset],
    retry_policy=RetryPolicy(max_retries=15),
)
def redis_service(context) -> Dict[str, str]:
    """Start Redis cache service."""
    _start_service(context, "redis")
    return {"status": "ready"}
    
    
@asset(
    name="opensearch",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[opensearch_image, update_secrets_asset],
    retry_policy=RetryPolicy(max_retries=15),
)
def opensearch_service(context) -> Dict[str, str]:
    """Start OpenSearch service."""
    _start_service(context, "opensearch")
    return {"status": "ready"}


@asset(
    name="weaviate",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[weaviate_image, update_secrets_asset],
    retry_policy=RetryPolicy(max_retries=15),
)
def weaviate_service(context) -> Dict[str, str]:
    """Start Weaviate vector database service."""
    _start_service(context, "weaviate")
    return {"status": "ready"}


@asset(
    name="seaweedfs",
    required_resource_keys={"compose_env", "process_checker"},
    deps=[seaweedfs_image, update_secrets_asset],
    retry_policy=RetryPolicy(max_retries=15),
)
def seaweedfs_service(context) -> Dict[str, str]:
    """Start SeaweedFS distributed storage service."""
    _start_service(context, "seaweedfs")
    return {"status": "ready"}


@asset(
    name="seaweedfs-init",
    required_resource_keys={"compose_env"},
    deps=[seaweedfs_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def seaweedfs_init_service(context) -> Dict[str, str]:
    """Initialize SeaweedFS buckets."""
    _run_init_container(context, "seaweedfs-init")
    return {"status": "completed"}


@asset(
    name="seaweedfs-init-autotest",
    required_resource_keys={"compose_env"},
    deps=[seaweedfs_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def seaweedfs_init_autotest_service(context) -> Dict[str, str]:
    """Initialize SeaweedFS buckets for autotest."""
    _run_init_container(context, "seaweedfs-init-autotest")
    return {"status": "completed"}


@asset(
    name="seaweedfs-init-mlflow",
    required_resource_keys={"compose_env"},
    deps=[seaweedfs_service],
    retry_policy=RetryPolicy(max_retries=15),
)
def seaweedfs_init_mlflow_service(context) -> Dict[str, str]:
    """Initialize SeaweedFS bucket for MLflow artifacts."""
    _run_init_container(context, "seaweedfs-init-mlflow")
    return {"status": "completed"}
