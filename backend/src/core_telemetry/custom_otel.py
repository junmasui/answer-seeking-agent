"""
Custom OpenTelemetry configuration and initialization.

This module provides manual OpenTelemetry setup with custom exporters
(Prometheus for metrics, Jaeger for traces) as a fallback when OpenLLMetry
is not available.

It exposes functions to initialize, configure, and shutdown telemetry for the application.

Features:
    - Resource attributes for service identification
    - Jaeger and OTLP exporters for distributed tracing
    - Prometheus and OTLP exporters for metrics collection
    - Auto-instrumentation for FastAPI, Celery, and Requests
    - Graceful shutdown of telemetry providers

Typical usage example:
    initialize_custom_telemetry()
    tracer = get_tracer()
    meter = get_meter()
    shutdown_telemetry()
"""

import logging

from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource

from core_telemetry.instrumentation import setup_auto_instrumentation
from core_telemetry.metrics import setup_metrics
from core_telemetry.tracing import setup_tracing

from .lib_config import get_lib_config

logger = logging.getLogger(__name__)

# Global telemetry configuration
_custom_telemetry_initialized = False


def get_telemetry_config():
    """
    Retrieve telemetry configuration from environment variables.

    Returns:
        dict: Dictionary containing telemetry configuration values such as service name, version, environment, endpoints, and feature flags.

    """
    return get_lib_config().otel


def initialize_custom_telemetry(**kwargs):
    """
    Initialize custom OpenTelemetry with configured exporters and auto-instrumentation.

    This function sets up resource attributes for service identification, tracing and metrics exporters, and auto-instruments common libraries.
    If already initialized, it will not re-initialize.

    Args:
        **kwargs: Optional overrides for telemetry configuration values.

    """
    global _custom_telemetry_initialized, _tracer, _meter

    if _custom_telemetry_initialized:
        logger.debug('Custom telemetry already initialized')
        return

    config = get_telemetry_config().model_dump(mode='python')

    # Override with provided kwargs
    config.update(kwargs)

    # Create resource with service information
    resource = Resource.create(
        {
            'service.name': config['service_name'],
            'service.version': config['service_version'],
            'deployment.environment': config['environment'],
            'telemetry.sdk.name': 'opentelemetry',
            'telemetry.sdk.language': 'python',
        }
    )

    # Initialize tracing
    if config['enable_tracing']:
        setup_tracing(resource, config)

    # Initialize metrics
    if config['enable_metrics']:
        setup_metrics(resource, config)

    # Auto-instrument common libraries
    setup_auto_instrumentation()

    _custom_telemetry_initialized = True
    logger.info('Custom OpenTelemetry initialized successfully')


def shutdown_telemetry():
    """
    Shutdown telemetry and flush remaining data.

    Gracefully shuts down tracer and meter providers, ensuring all telemetry data is exported.
    """
    global _custom_telemetry_initialized

    if not _custom_telemetry_initialized:
        return

    try:
        # Shutdown tracer provider
        tracer_provider = trace.get_tracer_provider()
        if hasattr(tracer_provider, 'shutdown'):
            tracer_provider.shutdown()

        # Shutdown meter provider
        meter_provider = metrics.get_meter_provider()
        if hasattr(meter_provider, 'shutdown'):
            meter_provider.shutdown()

        logger.info('Custom telemetry shutdown successfully')
    except Exception as e:
        logger.error(f'Error during custom telemetry shutdown: {e}')
    finally:
        _custom_telemetry_initialized = False
