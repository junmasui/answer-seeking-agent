from opentelemetry.distro import BaseDistro
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.environment_variables import OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
from typing import Collection
import os
import logging

from .lib_config import get_telemetry_config
from .metrics import setup_metrics
from .tracing import setup_tracing

logger = logging.getLogger(__name__)

class CustomDistro(BaseDistro):
    """Custom OpenTelemetry distro for FastAPI/Flask applications.
    
    
    A distro is a customized, pre-packaged version of OpenTelemetry components that provides
    opinionated defaults and simplified configuration. 

    Automatically sets up common components like SDK TracerProvider, BatchSpanProcessor,
    and OTLP SpanExporter
    """
    
    def _configure(self, **kwargs):
        """Configure the distro with custom settings."""

        logger.info('DISTRO _CONFIGURE %r', kwargs)
        print('DISTRO _CONFIGURE %r', kwargs)
        

        # Set default service name if not provided
        if not os.getenv("OTEL_SERVICE_NAME"):
            os.environ["OTEL_SERVICE_NAME"] = "my-instrumented-app"
            
        # Set default resource attributes
        if not os.getenv("OTEL_RESOURCE_ATTRIBUTES"):
            os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.version=1.0.0"
            
        # Configure default exporters if not set
        if not os.getenv("OTEL_TRACES_EXPORTER"):
            os.environ["OTEL_TRACES_EXPORTER"] = "otlp"
            
        if not os.getenv("OTEL_METRICS_EXPORTER"):
            os.environ["OTEL_METRICS_EXPORTER"] = "otlp"

        # Create resource with service information
        config = get_telemetry_config().model_dump(mode='python')
        resource = Resource.create(
            {
                'service.name': config['service_name'],
                'service.version': config['service_version'],
                'deployment.environment': config['environment'],
                'telemetry.sdk.name': 'opentelemetry',
                'telemetry.sdk.language': 'python',
            }
        )
        # resource = Resource.create({
        #     "service.name": os.getenv("OTEL_SERVICE_NAME", "unknown-service"),
        #     "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
        #     "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development"),
        # })
        


    @property
    def _excluded_instrumentations(self) -> Collection[str]:
        """Return instrumentations to exclude by default."""
        disabled = os.getenv(OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, "")
        return disabled.split(",") if disabled else []

