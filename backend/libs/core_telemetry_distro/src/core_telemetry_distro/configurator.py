import logging
import os

from opentelemetry.distro import OpenTelemetryConfigurator
from opentelemetry.sdk.resources import Resource

from .lib_config import get_telemetry_config

logger = logging.getLogger(__name__)


class CustomConfigurator(OpenTelemetryConfigurator):
    """
    Custom configurator for OpenTelemetry components.

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

        otel_env_vars = sorted([k for k in os.environ if k.startswith('OTEL_')])
        for k in otel_env_vars:
            v = os.environ[k]
            logger.info('%s: %s', k, v)
            print(f'ENV VAR {k}: {v}')

        # The OTEL_SERVICE_NAME environment variable is the canonical way to
        # specify the service name.
        # See: https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/#general-sdk-configuration
        #
        # The opentelemetry-instrument command wrapper will read this and other
        # environment variables and configure the OpenTelemetry SDK accordingly.
        # The call to super().configure() will perform this configuration.
        #

        super().configure(**kwargs)

        # We do not want a repeat of these issues. They were created because a dependency was
        # calling set_tracer_provider and set_meter_provider outside of the normal
        # SDK OpenTelemetry initialization flow:
        #   https://github.com/huggingface/transformers/issues/39143
        #   https://github.com/huggingface/transformers/issues/39115
        #   https://github.com/huggingface/transformers/pull/39422
        #

        logger.info('CONFIGURED PROVIDERS %s', type(self))

    def _parse_headers(self, headers_str: str) -> dict:
        """Parse OTLP headers from environment variable."""
        headers = {}
        if headers_str:
            for header in headers_str.split(','):
                key, value = header.split('=', 1)
                headers[key.strip()] = value.strip()
        return headers
