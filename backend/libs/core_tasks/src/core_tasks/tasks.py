import logging

from celery import Celery
from core import ingest_documents, reset_worker_data
from log_config_monitor import dump_logger_tree

from . import celeryconfig

from .event_handlers import setup_monitoring

logger = logging.getLogger(__name__)
celery_app = Celery(main=__name__)

# Load the configuration from the celeryconfig module
celery_app.config_from_object(celeryconfig)

setup_monitoring(celery_app)


@celery_app.task(name='ingest-docs')
def ingest_task(doc_ids=None):
    """
    Celery task to ingest documents by their IDs.

    Processes document ingestion asynchronously, converting uploaded documents into searchable
    content in the vector store.
    """
    return ingest_documents(doc_ids)


@celery_app.task(name='get-logger-tree')
def get_worker_logger_tree(include_all=False):
    """
    Celery task to retrieve the logger tree from the worker process.

    Returns the hierarchical structure of loggers configured in the worker, optionally including all
    loggers or just the configured ones.
    """
    return dump_logger_tree(include_all=include_all)


@celery_app.task(name='reset-data')
def reset_data_task():
    """
    Celery task to reset worker data and clean up staging areas.

    Handles the reset-data event by clearing temporary files and resetting worker-specific data
    structures to their initial state.
    """
    return reset_worker_data()
