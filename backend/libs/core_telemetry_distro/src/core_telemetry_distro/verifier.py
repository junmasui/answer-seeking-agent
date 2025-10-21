import logging

from opentelemetry._events import get_event_logger_provider
from opentelemetry._logs import get_logger_provider
from opentelemetry.metrics import get_meter_provider
from opentelemetry.trace import get_tracer_provider

from core_telemetry_distro.util import print_object_tree

logger = logging.getLogger(__name__)


def verify_distro():
    logger_provider = get_logger_provider()
    tree = print_object_tree(logger_provider)
    ##TODO logger.info('logger_provider\n%s', tree.getvalue())

    meter_provider = get_meter_provider()
    tree = print_object_tree(meter_provider)
    ##TODO logger.info('meter_provider\n%s', tree.getvalue())

    tracer_provider = get_tracer_provider()
    tree = print_object_tree(tracer_provider)
    ##TODO logger.info('tracer_provider\n%s', tree.getvalue())

    event_logger_provider = get_event_logger_provider()

    # Verify that the tracer is using a BatchSpanProcessor and that exporters
    # are configured to send to http://otel-collector. This uses guarded
    # introspection so it works across multiple OpenTelemetry SDK versions.
    try:
        span_processors = []

        # Common places where span processors may be stored depending on SDK
        if hasattr(tracer_provider, '_active_span_processor'):
            active = getattr(tracer_provider, '_active_span_processor')
            # MultiSpanProcessor exposes a list of processors on _span_processors
            if hasattr(active, '_span_processors'):
                span_processors = list(getattr(active, '_span_processors'))
            else:
                span_processors = [active]
        elif hasattr(tracer_provider, '_span_processors'):
            span_processors = list(getattr(tracer_provider, '_span_processors'))

        # Best-effort detection of BatchSpanProcessor
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        has_batch = any(
            isinstance(sp, BatchSpanProcessor) or sp.__class__.__name__ == 'BatchSpanProcessor'
            for sp in span_processors
        )

        if has_batch:
            logger.info('Tracer is using BatchSpanProcessor')
        else:
            logger.warning(
                'Tracer is NOT using BatchSpanProcessor; processors: %s',
                [sp.__class__.__name__ for sp in span_processors],
            )

        # Inspect exporters attached to span processors and look for endpoint
        endpoints = []
        for sp in span_processors:
            exporter = getattr(sp, '_exporter', None) or getattr(sp, 'exporter', None)
            # fallback attribute names
            if exporter is None:
                for attr in ('_span_exporter', '_exporters', 'exporter'):
                    if hasattr(sp, attr):
                        exporter = getattr(sp, attr)
                        break
            if exporter is None:
                continue

            exporters = exporter if isinstance(exporter, (list, tuple)) else [exporter]
            for ex in exporters:
                endpoint = None
                # common exporter attributes for endpoint/url
                for a in ('endpoint', '_endpoint', 'url', '_url', 'connection_string'):
                    if hasattr(ex, a):
                        endpoint = getattr(ex, a)
                        break
                endpoints.append((ex.__class__.__name__, endpoint))

        logger.info('Discovered exporters and endpoints: %r', endpoints)

        if any(ep and 'http://otel-collector' in str(ep) for _, ep in endpoints):
            logger.info('Exporters configured to send to http://otel-collector')
        else:
            logger.warning('No exporter found configured to http://otel-collector; endpoints=%r', endpoints)
    except Exception:
        logger.exception('failed verifying tracer exporters / processors')
