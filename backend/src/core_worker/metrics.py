from prometheus_client import (
    CollectorRegistry,
    GCCollector,
    PlatformCollector,
    ProcessCollector,
    multiprocess,
    start_wsgi_server,
)

from .app_config import get_app_config


def start_metrics(is_main_worker: bool):
    """
    Start the Prometheus metrics collection system for the Celery worker.

    Sets up collectors for garbage collection, process, and platform metrics. If this is the main
    worker, also starts a WSGI server to expose metrics.
    """
    prometheus_multiproc_dir = get_app_config().prometheus_multiproc_dir
    prometheus_multiproc_dir.mkdir(exist_ok=True)

    registry = CollectorRegistry()

    # Register predefined collectors
    GCCollector(registry=registry)
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)

    # NOTE: The multiprocess collector will register itself with the registry.
    multiprocess.MultiProcessCollector(registry=registry, path=str(prometheus_multiproc_dir))

    if is_main_worker:
        port = 8989
        # Start a synchronous webserver to expose the metrics. Underneath, this
        # webserver will run on its own thread.
        _httpd, _thread = start_wsgi_server(port, registry=registry)
        print(f'Prometheus metrics server started on port {port}')


def child_exit(child_pid):
    """
    Mark a child process as dead in the Prometheus multiprocess collector.

    Called when a child worker process exits to clean up metrics data.
    """
    prometheus_multiproc_dir = get_app_config().prometheus_multiproc_dir
    multiprocess.mark_process_dead(child_pid, path=prometheus_multiproc_dir)
