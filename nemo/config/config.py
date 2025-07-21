from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

print('IMPORTING CONFIG')

def init(app):
    print('EXECUTGING CONFIG.INIT')
    # Create tracer provider
    tracer_provider = TracerProvider()

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    tracer_provider = trace.get_tracer_provider()

    # Create Jaeger exporter
    ## jaeger_exporter = JaegerExporter(agent_host_name='jaeger', agent_port=6831, collector_endpoint='http://jaeger:14268/api/traces')
    otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
