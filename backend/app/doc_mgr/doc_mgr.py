import logging
import pprint

from sqlalchemy import func

from .model_ops import list_tracking_records, get_tracking_stats, update_tracking_record
from .model import create_tables_if_not_existing, drop_all_tables
from ..public_models import Document, DocumentList, DocumentStats, DocumentStatus

logger = logging.getLogger(__name__)

def documents_startup():
    create_tables_if_not_existing()

def documents_reset():
    drop_all_tables()
    create_tables_if_not_existing()


def list_documents(file_dir, start, length):
    """Return the list of files in cloud storage.
    """

    existing_objs = list_tracking_records(start, length)
    table_stats = get_tracking_stats()

    def _to_dict(_x):
        return Document(
            id = _x.id,
            status = _x.status,
            name = _x.filename,
            size_bytes = _x.size_bytes,
            modification_time = _x.file_modified_time,
            ingestion_time = _x.ingested_time
        )

    file_list = [_to_dict(x) for x in existing_objs]

    return DocumentList(
        documents = file_list,
        document_count = table_stats['doc_count'],
        table_updated_time = table_stats['max_update_time']
    )


def get_document_stats(file_dir):

    table_stats = get_tracking_stats()

    return DocumentStats(
        document_count = table_stats['doc_count'],
        table_updated_time = table_stats['max_update_time']
    )

def update_document_status(doc_uuid, status, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_tracking_record(doc_uuid=doc_uuid) as record:
        record.status = status
        if last_user_id:
            record.last_user_id = last_user_id
