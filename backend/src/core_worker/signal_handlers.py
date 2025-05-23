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

from core.signals import configure_sender, send_start_up
from log_config_monitor import get_logging_conf_monitor

from .metrics import child_exit, start_metrics

logger = logging.getLogger(__name__)


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    """
    See: https://celery.school/custom-celery-task-logger
    """
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter('%(asctime)s - %(task_id)s - %(task_name)s - %(name)s - %(levelname)s - %(message)s')
        )


@worker_init.connect
def handle_worker_init(**kwargs):
    logger.info('worker init')

    get_logging_conf_monitor().start()

    start_metrics(is_main_worker=True)

    configure_sender(is_worker=True)

    send_start_up()


@worker_ready.connect
def handle_worker_ready(**kwargs):
    logger.info('worker ready')


@worker_process_init.connect
def handle_worker_process_init(**kwargs):
    logger.info('worker process init')

    get_logging_conf_monitor().start()

    start_metrics(is_main_worker=False)


@worker_shutting_down.connect
def handle_worker_shutting_down(sig, how, exitcode, **kwargs):
    logger.info('worker process shutting down %s %s %s', sig, how, exitcode)

    get_logging_conf_monitor().stop()


@worker_process_shutdown.connect
def handle_worker_shutting_down(pid, exitcode, **kwargs):
    logger.info('worker process shutting down %s %s', pid, exitcode)

    child_exit(pid)

    get_logging_conf_monitor().stop()
