import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import select

from ...providers.sql_database import get_sessionmaker, DataDomain

from ..model import TrackedDocumentSet


logger = logging.getLogger(__name__)

def update_document_set(doc_set_uuid, is_new_doc_default=None, is_public_viewable=None, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_doc_set_record(doc_set_uuid=doc_set_uuid) as record:

        if is_new_doc_default is not None:
            record.is_new_doc_default = is_new_doc_default

        if is_public_viewable is not None:
            record.is_public_viewable = is_public_viewable

        if last_user_id:
            record.last_user_id = last_user_id



@contextmanager
def update_doc_set_record(doc_set_uuid):
    """Updates the document set.
    """
    if isinstance(doc_set_uuid, str):
        doc_set_uuid = uuid.UUID(hex=doc_set_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:

        with session.begin():
            stmt = select(TrackedDocumentSet).where(
                TrackedDocumentSet.id == doc_set_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one()

        with session.begin():
            yield existing_obj

