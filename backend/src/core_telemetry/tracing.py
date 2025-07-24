import logging
from typing import Optional

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from core_telemetry.custom_otel import _custom_telemetry_initialized, _tracer, initialize_custom_telemetry, logger


from opentelemetry.trace import trace

logger = logging.getLogger(__name__)

_tracer: Optional[trace.Tracer] = None


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.

    Returns:
        trace.Tracer: The global OpenTelemetry tracer instance.
    """
    if not _custom_telemetry_initialized:
        initialize_custom_telemetry()
    return _tracer


def setup_tracing(resource: Resource, config: dict):
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