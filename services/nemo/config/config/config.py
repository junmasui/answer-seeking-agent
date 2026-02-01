from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import Resource

print('IMPORTING CONFIG')

def init(app):
    print('EXECUTING CONFIG.INIT')
    # Create resource with custom attributes
    resource = Resource.create({
        "service.name": "nemo_guardrails",
        "service.version": "1.0",
        "env": "production"
    })
    
    # Create tracer provider with resource
    tracer_provider = TracerProvider(resource=resource)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    tracer_provider = trace.get_tracer_provider()

    # Create Zipkin exporter pointing to OTel Collector's Zipkin receiver
    zipkin_exporter = ZipkinExporter(endpoint="http://otel-collector:9411/api/v2/spans")

    # Add span processor
    span_processor = BatchSpanProcessor(zipkin_exporter)
    tracer_provider.add_span_processor(span_processor)
