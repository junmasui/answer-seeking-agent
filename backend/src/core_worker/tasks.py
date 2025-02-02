import logging
import importlib

from celery import Celery

from core import ingest_documents, reset_worker_data
from log_config_monitor import dump_logger_tree
from . import celeryconfig

logger = logging.getLogger(__name__)
celery_app = Celery(main=__name__)

# Load the configuration from the celeryconfig module
celery_app.config_from_object(celeryconfig)


@celery_app.task(name='ingest-docs')
def ingest_task(doc_ids=None):
    """Ingest
    """
    return ingest_documents(doc_ids)


@celery_app.task(name='get-logger-tree')
def get_worker_logger_tree(include_all=False):
    """Get the actual logger tree of the celery worker
    """
    return dump_logger_tree(include_all=include_all)


@celery_app.task(name='reset-data')
def reset_data_task():
    """Handles reset-data event.
    """
    return reset_worker_data()
