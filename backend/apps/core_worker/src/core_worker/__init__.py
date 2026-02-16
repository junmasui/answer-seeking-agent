import os

# Configure MLFlow to use the global OTel TracerProvider (from our Distro)
os.environ['MLFLOW_USE_DEFAULT_TRACER_PROVIDER'] = 'false'
# Enable Exemplars in OTel Metrics for trace correlation
os.environ['OTEL_METRICS_EXEMPLAR_FILTER'] = 'trace_based'

import early_init as _early_init  # noqa: I001, F401  ## loading this module configures environment and logging

from core_tasks import celery_app

from . import signal_handlers

# Explicitly define the exported names: these names are the contract of this module.
__all__ = ['celery_app', 'signal_handlers']
