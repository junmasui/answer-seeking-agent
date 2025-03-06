import logging

from sqlalchemy import func

from .model import TrackedDocument, TrackedDocumentSet
from .model_ops import (create_tables_if_not_existing,
                        drop_all_tables,
                        list_tracking_records,
                        get_tracking_stats,
                        list_tracking_document_sets,
                        update_tracking_record)
from ..public_models import Document, DocumentList, DocumentSet, DocumentSetList, DocumentStats

from ..signals import start_up_handler, reset_data_handler


logger = logging.getLogger(__name__)

@start_up_handler
def documents_startup(sender):
    if sender.is_worker:
        return
    create_tables_if_not_existing()


@reset_data_handler
def documents_reset(sender):
    if sender.is_worker:
        return
    drop_all_tables()
    create_tables_if_not_existing()


def list_document_sets(start, length):
    """Return the list of document sets.
    """

    existing_objs = list_tracking_document_sets(start=start, length=length)

    def _to_dict(_x: TrackedDocumentSet):
        return DocumentSet(
            id = _x.id,
            name = _x.name
        )

    doc_set_list = [_to_dict(x) for x in existing_objs]

    return DocumentSetList(
        document_sets = doc_set_list,
        document_set_count = 0
    )

def list_documents(file_dir, start, length):
    """Return the list of files in cloud storage.
    """

    existing_objs = list_tracking_records(start, length)
    table_stats = get_tracking_stats()

    def _to_dict(_x: TrackedDocument):
        return Document(
            id = _x.id,
            status = _x.status,
            name = _x.filename,
            size_bytes = _x.size_bytes,
            modification_time = _x.file_modified_time,
            ingestion_time = _x.ingested_time,
            document_set_id = _x.document_set.id,
            document_set_name = _x.document_set.name
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
