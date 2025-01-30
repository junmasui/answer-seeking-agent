from pathlib import Path

from prometheus_client import (multiprocess, start_wsgi_server,
                               generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST, Counter,
                               GCCollector, ProcessCollector, PlatformCollector)


def start_metrics(is_main_worker: bool):
    prometheus_multiproc_dir = Path('/tmp/prometheus_metrics')
    prometheus_multiproc_dir.mkdir(exist_ok=True)

    registry = CollectorRegistry()

    # Register predefined collectors
    GCCollector(registry=registry)
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)

    # NOTE: The multiprocess collector will register itself with the registry.
    multiprocess.MultiProcessCollector(
        registry=registry, path=str(prometheus_multiproc_dir))

    if is_main_worker:
        port = 8989
        # Start a synchronous webserver to expose the metrics. Underneath, this
        # webserver will run on its own thread.
        httpd, thread = start_wsgi_server(port, registry=registry)
        print(f'Prometheus metrics server started on port {port}')


def child_exit(child_pid):
    prometheus_multiproc_dir = Path('/tmp/prometheus_metrics')
    multiprocess.mark_process_dead(child_pid, path=prometheus_multiproc_dir)
