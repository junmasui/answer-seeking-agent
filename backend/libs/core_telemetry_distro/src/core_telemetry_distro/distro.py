import importlib.metadata as importlib_metadata
import logging
import os
import traceback
from typing import Collection

from opentelemetry.distro import OpenTelemetryDistro
from opentelemetry.instrumentation.environment_variables import OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.util._importlib_metadata import EntryPoint

logger = logging.getLogger(__name__)


class CustomDistro(OpenTelemetryDistro):
    """
    Custom OpenTelemetry distro for FastAPI/Flask applications.

    A distro is a customized, pre-packaged version of OpenTelemetry components that provides
    opinionated defaults and simplified configuration.

    Automatically sets up common components like SDK TracerProvider, BatchSpanProcessor,
    and OTLP SpanExporter
    """

    def _configure(self, **kwargs):
        """Configure the distro with custom settings."""
        logger.info('CONFIGURING DISTRO %s\n%s', type(self), kwargs)
        print('CONFIGURING DISTRO %s\n%s' % (type(self), kwargs))
        print(f'CALL STACK\n{"".join(traceback.format_stack())}')

        # Add "transformers" to the disabled list to prevent it from overriding the service name.
        disabled_instrumentations = os.environ.get('OTEL_PYTHON_DISABLED_INSTRUMENTATIONS', '').split(',')
        disabled_instrumentations = [item for item in disabled_instrumentations if item]  # Remove empty strings
        if 'transformers' not in disabled_instrumentations:
            disabled_instrumentations.append('transformers')
        if 'google_generativeai' not in disabled_instrumentations:
            disabled_instrumentations.append('google_generativeai')
        if 'weaviate_client' not in disabled_instrumentations:
            disabled_instrumentations.append('weaviate_client')
        os.environ['OTEL_PYTHON_DISABLED_INSTRUMENTATIONS'] = ','.join(disabled_instrumentations)

        # The DefaultDistro implementation already understands the standard OTEL environment
        # variables and will wire exporters, span processors, exporters endpoints, and
        # sampling according to those env vars.
        super()._configure(**kwargs)

        # Programmatically enable a sensible set of instrumentations by default.
        # This list is derived from the package dependencies declared in pyproject.toml
        # and includes common instrumentations we want enabled automatically.
        # Honor OTEL_PYTHON_DISABLED_INSTRUMENTATIONS via _excluded_instrumentations.
        wanted = [
            'custom_otel',
            'fastapi',
            'sqlalchemy',
            'httpx',
            'requests',
            'redis',
            'celery',
            'botocore',
            # "google_generativeai",
            'langchain',
            'openai',
            'system-metrics',
            # "transformers",
            # "weaviate_client",
        ]

        try:
            self._auto_instrument_entrypoints(wanted=wanted, **kwargs)
        except Exception:
            logger.exception('auto-instrumentation failed')

        logger.info('CONFIGURED DISTRO %s\n%s', type(self), kwargs)
        print('CONFIGURED DISTRO %s\n%s' % (type(self), kwargs))

    @property
    def _excluded_instrumentations(self) -> Collection[str]:
        """Return instrumentations to exclude by default."""
        disabled = os.getenv(OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, '')
        disabled_list = disabled.split(',') if disabled else []
        disabled_list.append('transformers')
        return disabled_list

    def load_instrumentor(self, entry_point: EntryPoint, skip_dep_check: bool = True, **kwargs):
        """
        Load and activate an instrumentation entry point.

        This method takes an instrumentation entry point and activates it by instantiating and
        calling instrument() on it. It is called for each opentelemetry_instrumentor entry point
        during auto-instrumentation.

        Distros can override this method to customize behavior, such as inspecting each entry point,
        passing additional arguments, loading a replacement, or skipping loading entirely.
        """
        logger.info('loading instrumentor %s', entry_point.name)
        print('LOADING INSTRUMENTOR %s' % entry_point.name)

        instrumentor_cls: type[BaseInstrumentor] = entry_point.load()
        self._auto_instrument(instrumentor_cls, skip_dep_check=skip_dep_check, **kwargs)

    def _auto_instrument(self, instrumentor_cls, **kwargs):
        """
        Instantiate an instrumentor class and call its instrument() method.

        Centralizes error handling and logging for instantiation+instrument calls.
        """
        try:
            instrumentor = instrumentor_cls()
            instrumentor.instrument(**kwargs)
        except Exception:
            logger.exception(
                'failed instantiating/instrumenting %s', getattr(instrumentor_cls, '__name__', str(instrumentor_cls))
            )

    def _auto_instrument_entrypoints(self, wanted: set[str], **kwargs) -> None:
        """
        Discover and instrument installed OpenTelemetry instrumentors.

        This method discovers all installed OpenTelemetry instrumentors and instruments the ones
        listed in `wanted`, unless they are excluded by the environment. It uses entry points only,
        ensuring consistent behavior with installed instrumentors.
        """
        disabled = {n.lower() for n in self._excluded_instrumentations}

        # Discover instrumentor entry points
        eps = []
        try:
            eps = importlib_metadata.entry_points(group='opentelemetry_instrumentor')
        except TypeError:
            # Older/newer importlib.metadata APIs differ; try a couple fallbacks.
            all_eps = importlib_metadata.entry_points()
            try:
                eps = all_eps.select(group='opentelemetry_instrumentor')
            except Exception:
                # Last resort: filter by attribute if present
                eps = [ep for ep in all_eps if getattr(ep, 'group', None) == 'opentelemetry_instrumentor']

        # Map entry point names to entry point objects for quick lookup
        ep_map = {ep.name.lower(): ep for ep in eps}

        for name in wanted:
            lname = name.lower()
            if lname in disabled:
                logger.info('instrumentation %s excluded via OTEL_PYTHON_DISABLED_INSTRUMENTATIONS', lname)
                continue

            # Use entry point-based instrumentor when available; otherwise skip.
            ep = ep_map.get(lname)
            if ep is None:
                logger.info('no instrumentor entry point found for %s; skipping', lname)
                continue

            logger.info('instrumenting %s via entry point', lname)
            try:
                instrumentor_cls = ep.load()
            except Exception:
                logger.exception('failed to load entry point %s', lname)
                continue

            self._auto_instrument(instrumentor_cls, **kwargs)
