import logging
from typing import Optional

import opentelemetry.metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_meter: Optional[opentelemetry.metrics.Meter] = None


def get_meter() -> opentelemetry.metrics.Meter:
    """
    Get the global meter instance.

    Returns:
        metrics.Meter: The global OpenTelemetry meter instance.

    """
    if not _meter:
        raise RuntimeError()
    return _meter


def setup_metrics(resource: Resource, config: dict):
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
    opentelemetry.metrics.set_meter_provider(meter_provider)
    logger.info('SET METER PROVIDER')

    _meter = opentelemetry.metrics.get_meter(__name__)

    logger.info('Metrics initialized with OTLP exporter')
