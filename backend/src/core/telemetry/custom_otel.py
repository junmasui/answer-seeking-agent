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
import os
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

logger = logging.getLogger(__name__)

# Global telemetry configuration
_custom_telemetry_initialized = False
_tracer: Optional[trace.Tracer] = None
_meter: Optional[metrics.Meter] = None


def get_telemetry_config():
    """
    Retrieve telemetry configuration from environment variables.

    Returns:
        dict: Dictionary containing telemetry configuration values such as service name, version, environment, endpoints, and feature flags.
    """
    return {
        'service_name': os.getenv('OTEL_SERVICE_NAME', 'answers-agent'),
        'service_version': os.getenv('OTEL_SERVICE_VERSION', '0.1.0'),
        'environment': os.getenv('OTEL_ENVIRONMENT', 'development'),
        'jaeger_endpoint': os.getenv('OTEL_EXPORTER_JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces'),
        'prometheus_port': int(os.getenv('OTEL_EXPORTER_PROMETHEUS_PORT', '8889')),
        'enable_tracing': os.getenv('OTEL_ENABLE_TRACING', 'true').lower() == 'true',
        'enable_metrics': os.getenv('OTEL_ENABLE_METRICS', 'true').lower() == 'true',
        'trace_sample_rate': float(os.getenv('OTEL_TRACE_SAMPLE_RATE', '1.0')),
    }


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

    config = get_telemetry_config()

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
        _setup_tracing(resource, config)

    # Initialize metrics
    if config['enable_metrics']:
        _setup_metrics(resource, config)

    # Auto-instrument common libraries
    _setup_auto_instrumentation()

    _custom_telemetry_initialized = True
    logger.info('Custom OpenTelemetry initialized successfully')


def _setup_tracing(resource: Resource, config: dict):
    """
    Set up distributed tracing with OTLP exporter.

    Configures the tracer provider, span processor, and global tracer for distributed tracing.

    Args:
        resource (Resource): OpenTelemetry resource describing the service.
        config (dict): Telemetry configuration dictionary.
    """
    global _tracer

    # Create Jaeger exporter
    ## jaeger_exporter = JaegerExporter(agent_host_name='jaeger', agent_port=6831, collector_endpoint='http://jaeger:14268/api/traces')

    otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(config['trace_sample_rate']))

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    _tracer = trace.get_tracer(__name__)

    logger.info(f'Tracing initialized with OTLP endpoint: {otlp_exporter}')


def _setup_metrics(resource: Resource, config: dict):
    """
    Set up metrics collection with OTLP exporter.

    Configures the meter provider, metric reader, and global meter for metrics collection.

    Args:
        resource (Resource): OpenTelemetry resource describing the service.
        config (dict): Telemetry configuration dictionary.
    """
    global _meter

    # Create OTLP metric exporter and wrap in a PeriodicExportingMetricReader
    otlp_exporter = OTLPMetricExporter(endpoint='http://otel-collector:4318/v1/metrics')
    otlp_reader = PeriodicExportingMetricReader(otlp_exporter)

    # Create meter provider
    meter_provider = MeterProvider(resource=resource, metric_readers=[otlp_reader])

    # Set global meter provider
    logger.info('SETTING METER PROVIDER')
    metrics.set_meter_provider(meter_provider)
    logger.info('SET METER PROVIDER')

    _meter = metrics.get_meter(__name__)

    logger.info('Metrics initialized with OTLP exporter')


def _setup_auto_instrumentation():
    """
    Set up auto-instrumentation for common libraries (FastAPI, Celery, Requests).

    Attempts to instrument supported libraries and logs any failures.
    """
    # try:
    #     # Instrument FastAPI
    #     FastAPIInstrumentor().instrument()
    #     logger.debug('FastAPI instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument FastAPI: {e}')

    # try:
    #     # Instrument Celery
    #     CeleryInstrumentor().instrument()
    #     logger.debug('Celery instrumentation enabled')
    # except Exception as e:
    #     logger.warning(f'Failed to instrument Celery: {e}')

    try:
        # Instrument Botocore requests
        BotocoreInstrumentor().instrument()
        logger.debug('Botocore instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Botocore: {e}')

    try:
        # Instrument HTTP requests
        RequestsInstrumentor().instrument()
        logger.debug('Requests instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Requests: {e}')

    try:
        # Instrument HTTPX requests
        HTTPXClientInstrumentor().instrument()
        logger.debug('Requests instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument Requests: {e}')

    try:
        # Instrument SQLAlchemy requests
        SQLAlchemyInstrumentor().instrument()
        logger.debug('SQLAlchemy instrumentation enabled')
    except Exception as e:
        logger.warning(f'Failed to instrument SQLAlchemy: {e}')


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.

    Returns:
        trace.Tracer: The global OpenTelemetry tracer instance.
    """
    if not _custom_telemetry_initialized:
        initialize_custom_telemetry()
    return _tracer


def get_meter() -> metrics.Meter:
    """
    Get the global meter instance.

    Returns:
        metrics.Meter: The global OpenTelemetry meter instance.
    """
    if not _custom_telemetry_initialized:
        initialize_custom_telemetry()
    return _meter


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
