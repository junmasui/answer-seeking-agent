"""Asset exports for all service assets."""

from .auth import keycloak_init_service, keycloak_service
from .autotest import (
    api_server_autotest_service,
    backend_autotest_dependency_gate_service,
    celery_worker_autotest_service,
    webui_server_autotest_service,
)
from .databases import (
    postgres_init_autotest_service,
    postgres_init_dependency_gate_service,
    postgres_init_service,
    postgres_keycloak_init_service,
    postgres_service,
)
from .images import (
    ALL_IMAGE_ASSETS,
    api_server_image,
    build_python_packages_asset,
    nemo_image,
    opensearch_image,
    redis_image,
    seaweedfs_image,
    slim_util_image,
    traefik_image,
    weaviate_image,
    webui_server_image,
)
from .infrastructure import (
    opensearch_service,
    redis_service,
    seaweedfs_init_autotest_service,
    seaweedfs_init_service,
    seaweedfs_service,
    weaviate_service,
)
from .observability import (
    grafana_service,
    jaeger_service,
    loki_service,
    otel_collector_docker_service,
    otel_collector_service,
    prometheus_service,
)
from .scripts import initialize_environment_asset
from .services import (
    api_server_service,
    celery_worker_service,
    dev_server_service,
    nemo_guardrails_service,
    presidio_analyzer_service,
    slim_util_service,
    traefik_service,
    webui_server_service,
)

__all__ = [
    # Images
    "ALL_IMAGE_ASSETS",
    "slim_util_image",
    "seaweedfs_image",
    "redis_image",
    "opensearch_image",
    "traefik_image",
    "weaviate_image",
    "api_server_image",
    "build_python_packages_asset",
    "nemo_image",
    "webui_server_image",
    # Databases
    "postgres_service",
    "postgres_init_dependency_gate_service",
    "postgres_init_service",
    "postgres_keycloak_init_service",
    "postgres_init_autotest_service",
    # Infrastructure
    "redis_service",
    "opensearch_service",
    "weaviate_service",
    "seaweedfs_service",
    "seaweedfs_init_service",
    "seaweedfs_init_autotest_service",
    # Auth
    "keycloak_service",
    "keycloak_init_service",
    # Observability
    "prometheus_service",
    "grafana_service",
    "jaeger_service",
    "loki_service",
    "otel_collector_service",
    "otel_collector_docker_service",
    # Services
    "traefik_service",
    "slim_util_service",
    "api_server_service",
    "celery_worker_service",
    "nemo_guardrails_service",
    "presidio_analyzer_service",
    "webui_server_service",
    "dev_server_service",
    # Autotest
    "backend_autotest_dependency_gate_service",
    "api_server_autotest_service",
    "celery_worker_autotest_service",
    "webui_server_autotest_service",
    # Scripts
    "initialize_environment_asset",
    "build_python_packages_asset",
]
