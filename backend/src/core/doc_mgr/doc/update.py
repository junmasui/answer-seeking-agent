import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import select

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import TrackedDocument


logger = logging.getLogger(__name__)




def update_document_status(doc_uuid, status, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_tracking_record(doc_uuid=doc_uuid) as record:
        record.status = status
        if last_user_id:
            record.last_user_id = last_user_id



def update_document(doc_uuid, doc_set_uuid=None, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_tracking_record(doc_uuid=doc_uuid) as record:

        if doc_set_uuid is not None:
            record.document_set_id = doc_set_uuid

        if last_user_id:
            record.last_user_id = last_user_id



@contextmanager
def update_tracking_record(doc_uuid):
    """Updates the tracking record for the document.
    """
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:

        with session.begin():
            stmt = select(TrackedDocument).where(
                TrackedDocument.id == doc_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one()

        with session.begin():
            yield existing_obj

