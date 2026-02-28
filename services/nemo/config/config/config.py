import logging

logger = logging.getLogger(__name__)


def init(app):
    # Tracing is handled entirely by the opentelemetry-instrument CLI wrapper
    # and the env vars in opentelemetry-instrument.env.  Do NOT create a second
    # TracerProvider or exporter here — that causes every span to be exported
    # twice (once via OTLP, once via Zipkin) resulting in duplicate span IDs
    # in Jaeger and broken span nesting.
    logger.info('nemo guardrails config.init (tracing configured via opentelemetry-instrument CLI)')
