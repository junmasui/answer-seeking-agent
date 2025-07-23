import logging

from celery.app.log import TaskFormatter
from celery.signals import (
    after_setup_task_logger,
    worker_init,
    worker_process_init,
    worker_process_shutdown,
    worker_ready,
    worker_shutting_down,
)
from opentelemetry.instrumentation.celery import CeleryInstrumentor

from core_telemetry import init_telemetry
from core.signals import configure_sender, send_start_up
from log_config_monitor import get_logging_conf_monitor

from .metrics import child_exit, start_metrics

logger = logging.getLogger(__name__)


@after_setup_task_logger.connect
def setup_task_logger(logger, *_args, **_kwargs):
    """
    Configures the task logger format.

    See: https://celery.school/custom-celery-task-logger
    """
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter('%(asctime)s - %(task_id)s - %(task_name)s - %(name)s - %(levelname)s - %(message)s')
        )


@worker_init.connect
def handle_worker_init(**_kwargs):
    """
    Handles worker initialization.

    Sets up logging monitor, metrics collection, configures sender as worker, and sends startup
    signal when the main worker process initializes.
    """
    logger.info('worker init')

    get_logging_conf_monitor().start()

    # init_celery_telemetry()

    # start_metrics(is_main_worker=True)

    configure_sender(is_worker=True)

    send_start_up()


@worker_ready.connect
def handle_worker_ready(**_kwargs):
    """
    Handles worker ready signal.

    Called when the worker is ready to receive tasks. Logs the worker ready status for monitoring
    purposes.
    """
    logger.info('worker ready')


@worker_process_init.connect
def handle_worker_process_init(**_kwargs):
    """
    Handle worker process initialization signal.

    Sets up logging monitor and metrics collection for child worker processes. Called when a new
    worker process is spawned in a multiprocessing setup.
    """
    logger.info('worker process init')

    get_logging_conf_monitor().start()

    logger.info('INITIALIZING TELEMETRY')

    init_telemetry()

    start_metrics(is_main_worker=False)


@worker_shutting_down.connect
def handle_worker_shutting_down(sig, how, exitcode, **_kwargs):
    """
    Handle worker shutdown signal.

    Called when the main worker is shutting down. Stops the logging configuration monitor and logs
    shutdown details including signal, method, and exit code.
    """
    logger.info('worker process shutting down %s %s %s', sig, how, exitcode)

    get_logging_conf_monitor().stop()


@worker_process_shutdown.connect
def handle_worker_process_shutting_down(pid, exitcode, **_kwargs):
    """
    Handle worker process shutdown signal.

    Called when a child worker process shuts down. Marks the process as dead in metrics collection
    and stops the logging configuration monitor.
    """
    logger.info('worker process shutting down %s %s', pid, exitcode)

    child_exit(pid)

    get_logging_conf_monitor().stop()
