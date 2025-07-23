import logging
import gc
import threading
import os

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.metrics import set_meter_provider, get_meter_provider
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.metrics import Observation

import psutil

from .app_config import get_app_config


logger = logging.getLogger(__name__)

def start_metrics(is_main_worker: bool):
    """
    Start the Prometheus metrics collection system for the Celery worker.

    Sets up collectors for garbage collection, process, and platform metrics. If this is the main
    worker, also starts a WSGI server to expose metrics.
    """
    provider = get_meter_provider()

    meter = provider.get_meter("celery-worker")

    if is_main_worker:
        # Instrument system metrics (CPU, memory, etc.)
        SystemMetricsInstrumentor().instrument(meter_provider=provider)

    # GC objects count
    def gc_objects_callback(options):
        return [Observation(len(gc.get_objects()))]
    meter.create_observable_gauge(
        "python_gc_objects",
        callbacks=[gc_objects_callback],
        description="Number of objects tracked by Python GC"
    )

    # Memory usage (RSS)
    def memory_usage_callback(options):
        if psutil:
            process = psutil.Process(os.getpid())
            return [Observation(process.memory_info().rss)]
        return [Observation(0)]
    meter.create_observable_gauge(
        "python_process_memory_bytes",
        callbacks=[memory_usage_callback],
        description="Resident memory size in bytes"
    )

    # Thread count
    def thread_count_callback(options):
        return [Observation(threading.active_count())]
    meter.create_observable_gauge(
        "python_thread_count",
        callbacks=[thread_count_callback],
        description="Number of active threads"
    )


def child_exit(child_pid):
    """
    Mark a child process as dead in the Prometheus multiprocess collector.

    Called when a child worker process exits to clean up metrics data.
    """
