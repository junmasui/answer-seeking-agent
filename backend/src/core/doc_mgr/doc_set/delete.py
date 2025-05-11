import logging
import uuid

from sqlalchemy import delete

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import DbTrackedDocumentSet

from .query import get_document_sets


logger = logging.getLogger(__name__)

def delete_document_set(document_set_id):
    """Delete document set
    """

    # Retrieve tracking record.

    doc_set_records = get_document_sets(doc_set_uuid_list=[document_set_id])
    if not doc_set_records:
        return False

    doc_set_record = doc_set_records[0]

    # Delete tracking record.

    _delete_tracking_record(doc_set_record.id)

    return True


def _delete_tracking_record(doc_set_uuid):
    """Deletes the tracking record.
    """
    if isinstance(doc_set_uuid, str):
        doc_set_uuid = uuid.UUID(hex=doc_set_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:

        with session.begin():
            stmt = delete(DbTrackedDocumentSet).where(
                DbTrackedDocumentSet.id == doc_set_uuid)
            result = session.execute(stmt)
