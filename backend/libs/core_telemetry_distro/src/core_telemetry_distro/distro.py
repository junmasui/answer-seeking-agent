from opentelemetry.distro import OpenTelemetryDistro

from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.environment_variables import OTEL_PYTHON_DISABLED_INSTRUMENTATIONS
from typing import Collection
import os
import logging
import traceback

import importlib.metadata as importlib_metadata

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.util._importlib_metadata import EntryPoint

from .lib_config import get_telemetry_config

logger = logging.getLogger(__name__)

class CustomDistro(OpenTelemetryDistro):
    """Custom OpenTelemetry distro for FastAPI/Flask applications.
    
    
    A distro is a customized, pre-packaged version of OpenTelemetry components that provides
    opinionated defaults and simplified configuration. 

    Automatically sets up common components like SDK TracerProvider, BatchSpanProcessor,
    and OTLP SpanExporter
    """
    
    def _configure(self, **kwargs):
        """Configure the distro with custom settings."""

        logger.info('CONFIGURING DISTRO %s\n%s', type(self), kwargs)
        print('CONFIGURING DISTRO %s\n%s' % (type(self), kwargs))
        print(''.join(traceback.format_stack()))

        for k,v in os.environ.items():
            if k.startswith('OTEL_'):
                logger.info('%s: %s', k, v)

        # The OTEL_SERVICE_NAME environment variable is the canonical way to
        # specify the service name.
        # See: https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/#general-sdk-configuration
        #
        # The opentelemetry-instrument command wrapper will read this and other
        # environment variables and configure the OpenTelemetry SDK accordingly.
        # The call to super()._configure() will perform this configuration.
        #
        # The following code is no longer needed because we can rely on the
        # standard environment variable handling.
        #
        # if not os.getenv("OTEL_SERVICE_NAME"):
        #     os.environ["OTEL_SERVICE_NAME"] = "answers_api_server"
        # print(f'ENVIRON OTEL_SERVICE_NAME {os.environ["OTEL_SERVICE_NAME"]}')
        # os.environ["OTEL_SERVICE_NAME"] = "answers_api_server"
            
        # if not os.getenv("OTEL_RESOURCE_ATTRIBUTES"):
        #     os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.name=answers_api_server,service.version=1.0.0"
        # print(f'ENVIRON OTEL_RESOURCE_ATTRIBUTES {os.environ["OTEL_RESOURCE_ATTRIBUTES"]}')
        # os.environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.name=answers_api_server,service.version=1.0.0"
            
        # Configure default exporters if not set
        if not os.getenv("OTEL_TRACES_EXPORTER"):
            os.environ["OTEL_TRACES_EXPORTER"] = "otlp"
            
        if not os.getenv("OTEL_METRICS_EXPORTER"):
            os.environ["OTEL_METRICS_EXPORTER"] = "otlp"

        # The DefaultDistro implementation already understands the standard OTEL environment variables
        # and will wire exporters, span processors, exporters endpoints, and sampling according
        # to those env vars.
        super()._configure(**kwargs)

        # Programmatically enable a sensible set of instrumentations by default.
        # This list is derived from the package dependencies declared in pyproject.toml
        # and includes common instrumentations we want enabled automatically.
        # Honor OTEL_PYTHON_DISABLED_INSTRUMENTATIONS via _excluded_instrumentations.
        wanted = {
            "custom_otel",
            "fastapi",
            "sqlalchemy",
            "httpx",
            "requests",
            "redis",
            "celery",
            "botocore",
            # "google-generativeai",
            "langchain",
            "openai",
            "system-metrics",
            "transformers",
            # "weaviate",
        }

        try:
            self._auto_instrument(wanted=wanted, **kwargs)
        except Exception:
            logger.exception("auto-instrumentation failed")


    @property
    def _excluded_instrumentations(self) -> Collection[str]:
        """Return instrumentations to exclude by default."""
        disabled = os.getenv(OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, "")
        return disabled.split(",") if disabled else []

    def load_instrumentor(
        self, entry_point: EntryPoint, skip_dep_check: bool =True, **kwargs
    ):
        """Takes an instrumentation entry point and activates it by instantiating
        and calling instrument() on it.
        This is called for each opentelemetry_instrumentor entry point by auto
        instrumentation.

        Distros can override this method to customize the behavior by
        inspecting each entry point and configuring them in special ways,
        passing additional arguments, load a replacement/fork instead,
        skip loading entirely, etc.
        """

        logger.info('loading instrumentor %s', entry_point.name)
        print('LOADING INSTRUMENTOR %s'% entry_point.name)

        instrumentor: BaseInstrumentor = entry_point.load()
        instrumentor().instrument(skip_dep_check=skip_dep_check, **kwargs)

    def _auto_instrument(self, wanted: set[str], **kwargs) -> None:
        """Discover installed opentelemetry instrumentors and instrument the
        ones listed in `wanted` unless they are excluded by env.

        This uses entry points only; explicit import fallback logic has been removed
        to keep behavior consistent with installed instrumentors and entry points.
        """
        disabled = {n.lower() for n in self._excluded_instrumentations}

        # Discover instrumentor entry points
        eps = []
        try:
            eps = importlib_metadata.entry_points(group="opentelemetry_instrumentor")
        except TypeError:
            # Older/newer importlib.metadata APIs differ; try a couple fallbacks.
            all_eps = importlib_metadata.entry_points()
            try:
                eps = all_eps.select(group="opentelemetry_instrumentor")
            except Exception:
                # Last resort: filter by attribute if present
                eps = [ep for ep in all_eps if getattr(ep, 'group', None) == 'opentelemetry_instrumentor']

        # Map entry point names to entry point objects for quick lookup
        ep_map = {ep.name.lower(): ep for ep in eps}

        for name in wanted:
            lname = name.lower()
            if lname in disabled:
                logger.info("instrumentation %s excluded via OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", lname)
                continue

            # Use entry point-based instrumentor when available; otherwise skip.
            ep = ep_map.get(lname)
            if ep is None:
                logger.info("no instrumentor entry point found for %s; skipping", lname)
                continue

            try:
                logger.info("instrumenting %s via entry point", lname)
                instrumentor_cls = ep.load()
                instrumentor = instrumentor_cls()
                instrumentor.instrument(**kwargs)
            except Exception:
                logger.exception("failed instrumenting %s via entry point", lname)
