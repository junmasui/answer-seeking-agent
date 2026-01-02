import logging

from core_db.doc_mgr.doc.update import update_tracking_record

logger = logging.getLogger(__name__)


async def update_document_status(doc_uuid, status, last_user_id=None):
    """Updates status field with option to update."""
    async with update_tracking_record(doc_uuid=doc_uuid) as record:
        if record is None:
            return

        record.status = status
        if last_user_id:
            record.last_user_id = last_user_id


async def update_document(doc_uuid, doc_set_uuid=None, last_user_id=None):
    """Updates status field with option to update."""
    async with update_tracking_record(doc_uuid=doc_uuid) as record:
        if record is None:
            return

        if doc_set_uuid is not None:
            record.document_set_id = doc_set_uuid

        if last_user_id:
            record.last_user_id = last_user_id
