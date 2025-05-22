from pathlib import Path

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    GCCollector,
    PlatformCollector,
    ProcessCollector,
    generate_latest,
    multiprocess,
    start_wsgi_server,
)

from global_config import get_global_config

def start_metrics(is_main_worker: bool):
    prometheus_multiproc_dir = get_global_config().celery_worker.prometheus_multiproc_dir
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
        httpd, thread = start_wsgi_server(port, registry=registry)
        print(f'Prometheus metrics server started on port {port}')


def child_exit(child_pid):
    prometheus_multiproc_dir = get_global_config().celery_worker.prometheus_multiproc_dir
    multiprocess.mark_process_dead(child_pid, path=prometheus_multiproc_dir)
