"""
Real-time monitoring of Celery events.

This module provides a mechanism to monitor Celery worker and task events
in real-time. It uses a background thread to listen for events and can be
used to trigger actions based on the state of the Celery cluster.

The primary use case is for monitoring, not for customizing task or worker
lifecycles, for which Celery signals are more appropriate.

See Also:
    https://docs.celeryq.dev/en/stable/userguide/monitoring.html#real-time-processing

"""

import logging
import threading
from uuid import UUID

from celery import Celery
from celery.signals import worker_init, worker_shutting_down

from core import update_document_status
from core.public_models import DocumentStatus

logger = logging.getLogger(__name__)

# Real-time monitoring with Celery events.
#
# Our use case is monitoring. We are not customizing additional processing on the task
# or worker lifecycles, which would be the use cases for Celery signals. Hence we
# use Celery events.
#
# See: https://github.com/celery/celery/blob/main/docs/userguide/monitoring.rst#real-time-processing
#


class CeleryMonitoringThread:
    """
    Manages a background thread for monitoring Celery events.

    This class encapsulates the logic for starting and stopping a thread that
    listens for Celery events. It is designed to be controlled by Celery worker
    signals to ensure clean startup and shutdown.

    Attributes:
        celery_app: The Celery application instance.
        state: The Celery event state object.
        thread: The background monitoring thread.
        connection: The connection to the message broker for reading events.
        receiver: The Celery event receiver.

    """

    def __init__(self, celery_app: Celery):
        """
        Initializes the CeleryMonitoringThread.

        Args:
            celery_app: The Celery application instance.

        """
        self.celery_app = celery_app
        self.state = celery_app.events.State()
        self.thread = None
        self.connection = None
        self.receiver = None

    def start(self):
        """Starts the monitoring thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """The main loop for the monitoring thread."""
        self.connection = self.celery_app.connection_for_read()
        self.receiver = self.celery_app.events.Receiver(
            self.connection,
            handlers={
                'worker-online': self._on_worker_online,
                'worker-offline': self._on_worker_offline,
                'task-sent': self._on_task_sent,
                '*': self.state.event,
            },
        )
        # The capture call is blocking and will run until the connection is closed.
        self.receiver.capture(limit=None, timeout=None, wakeup=True)

    def stop(self):
        """Stops the monitoring thread gracefully."""
        if self.connection:
            self.connection.close()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

    def _on_worker_online(self, event):
        """
        Logs when a Celery worker comes online and updates state tracking.

        Args:
            event: The worker-online event.

        """
        try:
            self.state.event(event)
            logger.info('Worker is online: %s', event)
        except Exception as ex:
            logger.warning('Error during working-online event', exc_info=ex)

    def _on_worker_offline(self, event):
        """
        Logs when a Celery worker goes offline and updates state tracking.

        Args:
            event: The worker-offline event.

        """
        try:
            self.state.event(event)
            logger.info('Worker is offline: %s', event)
        except Exception as ex:
            logger.warning('Error during working-off event', exc_info=ex)

    def _safe_eval_kwargs(self, kwargs_str: str):
        """
        Safely evaluates a string representation of kwargs, allowing for UUID objects.

        Args:
            kwargs_str: The string representation of the keyword arguments.

        Returns:
            The evaluated keyword arguments as a dictionary.

        """
        # eval() can be dangerous if used with untrusted input. However, in this case,
        # we are controlling the environment by providing a restricted globals dictionary.
        # We only make the UUID constructor available, which is needed to parse the
        # kwargs string from Celery events.
        safe_globals = {'UUID': UUID}
        return eval(kwargs_str, {'__builtins__': {}}, safe_globals)

    def _on_task_sent(self, event):
        """
        Logs when a task is sent and updates document status to QUEUED.

        Args:
            event: The task-sent event.

        """
        try:
            self.state.event(event)

            logger.info('Task sent: %s', self.state)
            logger.info('Task sent: %s', self.state.tasks)

            task = self.state.tasks.get(event['uuid'])

            logger.info('Task sent: %s', event)
            logger.info('Task sent: %s', task)
            logger.info('Task sent: %s', task.kwargs)

            if task.name == 'ingest-docs':
                # The `ingest-docs` task is called with a `doc_ids` keyword argument.
                #
                # When a task is sent, Celery serializes the keyword arguments into a string
                # representation. We use a custom safe evaluation function to deserialize
                # the string back into a dictionary.
                # See: https://github.com/celery/celery/blob/main/celery/app/amqp.py#L322
                kwargs = self._safe_eval_kwargs(task.kwargs)
                doc_ids = kwargs.get('doc_ids')
                if doc_ids:
                    for doc_id in doc_ids:
                        update_document_status(doc_id, DocumentStatus.QUEUED)

            logger.info('Task sent: %s[%s] %s', task.name, task.uuid, task.info())
        except Exception as ex:
            logger.warning('Error during task-sent event', exc_info=ex)


def setup_monitoring(celery_app: Celery):
    """
    Sets up the Celery monitoring thread.

    This function creates a `CeleryMonitoringThread` instance and connects
    the worker initialization and shutdown signals to start and stop the
    monitoring thread.

    Args:
        celery_app: The Celery application instance.

    """
    monitor_thread = CeleryMonitoringThread(celery_app)

    @worker_init.connect(weak=False)
    def start_monitoring_thread(**kwargs):
        """Signal handler to start the monitoring thread when the worker initializes."""
        logger.info('Starting Celery event monitoring thread.')
        monitor_thread.start()

    @worker_shutting_down.connect(weak=False)
    def stop_monitoring_thread(sig, how, exitcode, **kwargs):
        """Signal handler to stop the monitoring thread when the worker shuts down."""
        logger.info('Stopping Celery event monitoring thread.')
        monitor_thread.stop()
