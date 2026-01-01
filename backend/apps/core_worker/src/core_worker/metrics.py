import gc
import logging
import os
import threading

import psutil
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.metrics import Observation, get_meter_provider

logger = logging.getLogger(__name__)


def start_metrics(is_main_worker: bool):
    """
    Start the Prometheus metrics collection system for the Celery worker.

    Sets up collectors for garbage collection, process, and platform metrics. If this is the main
    worker, also starts a WSGI server to expose metrics.
    """
    provider = get_meter_provider()

    meter = provider.get_meter('celery-worker')

    if is_main_worker:
        # Instrument system metrics (CPU, memory, etc.)
        SystemMetricsInstrumentor().instrument(meter_provider=provider)

    # GC stats (lighter weight than specific object counts)
    def gc_stats_callback(options):
        # gc.get_stats() returns a list of 3 dicts (one for each generation)
        # keys: 'collections', 'collected', 'uncollectable'
        stats = gc.get_stats()
        observations = []
        for generation, stat in enumerate(stats):
            observations.append(Observation(stat['collected'], {'generation': str(generation), 'type': 'collected'}))
            observations.append(
                Observation(stat['collections'], {'generation': str(generation), 'type': 'collections'})
            )
        return observations

    meter.create_observable_counter(
        'python_gc_stats',
        callbacks=[gc_stats_callback],
        description='Statistics from the Python Garbage Collector (collections and items collected)',
    )

    # Memory usage (RSS)
    def memory_usage_callback(options):
        if psutil:
            process = psutil.Process(os.getpid())
            return [Observation(process.memory_info().rss)]
        return [Observation(0)]

    meter.create_observable_gauge(
        'python_process_memory_bytes', callbacks=[memory_usage_callback], description='Resident memory size in bytes'
    )

    # Thread count
    def thread_count_callback(options):
        return [Observation(threading.active_count())]

    meter.create_observable_gauge(
        'python_thread_count', callbacks=[thread_count_callback], description='Number of active threads'
    )


def child_exit(child_pid):
    """
    Mark a child process as dead in the Prometheus multiprocess collector.

    Called when a child worker process exits to clean up metrics data.
    """
