import logging

from core_db.doc_mgr.doc_set.delete import delete_tracking_record

from core_db.doc_mgr.doc_set.query import get_document_sets

logger = logging.getLogger(__name__)

def delete_document_set(document_set_id):
    """Delete document set."""
    # Retrieve tracking record.

    doc_set_records = get_document_sets(doc_set_uuid_list=[document_set_id])
    if not doc_set_records:
        return False

    doc_set_record = doc_set_records[0]

    # Delete tracking record.

    delete_tracking_record(doc_set_record.id)

    return True


