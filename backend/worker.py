import early_config  # noqa: F401 ## loading this module configures environment and logging

import logging
import importlib

from celery import Celery
from celery.signals import worker_shutting_down

from app import ingest_documents, update_document_status
from app.public_models import DocumentStatus

logger = logging.getLogger(__name__)


# @celeryd_init.connect
# def worker_init(sender, instance, **kwargs):
#     logger.warning('worker init %s %s', sender, instance)

@worker_shutting_down.connect
def worker_shutting_down(sig, how, exitcode, **kwargs):
    logger.warning('worker shutting down %s %s %s', sig, how, exitcode)

# Real-time monitoring with Celery events.
#
# Our use case is monitoring. We are not customizing additional processing on the task or worker lifecycles,
# which would be the use cases for Celery signals. Hence we use Celery events.
#
# See: https://github.com/celery/celery/blob/main/docs/userguide/monitoring.rst#real-time-processing
#


def setup_monitoring(app):
    # A State builds an In-memory representation of cluster state from the event stream.
    state = app.events.State()

    def announce_worker_online(event):
        #
        state.event(event)

        logger.info('Worker is online: %s', event['name'])

    def announce_worker_offline(event):
        #
        state.event(event)

        logger.info('Worker is offline: %s', event['name'])

    def announce_sent_tasks(event):
        state.event(event)

        # task name is sent only with -received event, and state
        # will keep track of this for us.
        task = state.tasks.get(event['uuid'])

        update_document_status(event['uuid'], DocumentStatus.QUEUED)

        logger.info('Task sent: %s[%s] %s', task.name, task.uuid, task.info())

    with app.connection() as connection:
        recv = app.events.Receiver(connection,
                                   handlers={
                                       'worker-online': announce_worker_online,
                                       'worker-offline': announce_worker_offline,
                                       'task-sent': announce_sent_tasks,
                                       '*': state.event,
                                   })
        recv.capture(limit=None, timeout=None, wakeup=True)


app = Celery(main=__name__)

# Load the configuration from the celeryconfig.py file
celeryconfig = importlib.import_module('celeryconfig')
app.config_from_object(celeryconfig)


@app.task(name='ingest-files')
def ingest_task(doc_ids=None):
    """Ingest
    """
    return ingest_documents(doc_ids)
