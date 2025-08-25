import os
from opentelemetry.distro import OpenTelemetryConfigurator
from opentelemetry.sdk.resources import Resource
import logging

from .lib_config import get_telemetry_config

logger = logging.getLogger(__name__)

class CustomConfigurator(OpenTelemetryConfigurator):
    """Custom configurator for OpenTelemetry components.
    
    A configurator is a more focused component that handles specific configuration aspects of the
    OpenTelemetry setup. It's responsible for fine-tuning how telemetry data is collected,
    processed, and exported.
    """
    
    def configure(self, **kwargs):
        """Configure OpenTelemetry SDK with custom settings."""

        logger.info('CONFIGURING CONFIGURATOR %s\n%s', type(self), kwargs)
        print('CONFIGURING CONFIGURATOR %s\n%s' % (type(self), kwargs))
        
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

        for k in sorted(os.environ.keys()):
            if k.startswith('OTEL_'):
                v = os.environ[k]
                logger.info('%s: %s', k, v)
                print(f'{k}: {v}')

        super().configure(**kwargs)

        # Initialize tracing
        # if config['enable_tracing']:
        #     setup_tracing(resource, config)

        #     print('CONFIGURATOR CONFIGURED TRACING')

        # # Initialize metrics
        # if config['enable_metrics']:
        #     setup_metrics(resource, config)

        #     print('CONFIGURATOR CONFIGURED METRICS')

        # setup_auto_instrumentation()
        # print('CONFIGURATOR CONFIGURED INSTRUMENTATION')
        # resource = Resource.create(
        #     {
        #         'service.name': config['service_name'],
        #         'service.version': config['service_version'],
        #         'deployment.environment': config['environment'],
        #         'telemetry.sdk.name': 'opentelemetry',
        #         'telemetry.sdk.language': 'python',
        #     }
        # )
        # resource = Resource.create({
        #     "service.name": os.getenv("OTEL_SERVICE_NAME", "unknown-service"),
        #     "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
        #     "deployment.environment": os.getenv("DEPLOYMENT_ENV", "development"),
        # })
        

        # # Configure tracing
        # tracer_provider = TracerProvider(resource=resource)
        
        # # Add span processor with OTLP exporter
        # otlp_exporter = OTLPSpanExporter(
        #     endpoint=os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4317"),
        #     headers=self._parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")),
        # )
        
        # span_processor = BatchSpanProcessor(otlp_exporter)
        # tracer_provider.add_span_processor(span_processor)
        
        # # Set global tracer provider
        # trace.set_tracer_provider(tracer_provider)
        
        # # Configure metrics
        # metric_reader = PeriodicExportingMetricReader(
        #     OTLPMetricExporter(
        #         endpoint=os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4317"),
        #         headers=self._parse_headers(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")),
        #     ),
        #     export_interval_millis=30000,  # 30 seconds
        # )
        
        # meter_provider = MeterProvider(
        #     resource=resource,
        #     metric_readers=[metric_reader]
        # )
        
        # metrics.set_meter_provider(meter_provider)
    
    def _parse_headers(self, headers_str: str) -> dict:
        """Parse OTLP headers from environment variable."""
        headers = {}
        if headers_str:
            for header in headers_str.split(","):
                key, value = header.split("=", 1)
                headers[key.strip()] = value.strip()
        return headers

