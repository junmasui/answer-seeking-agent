import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from ...db_models import DbTrackedDocumentSet
from ...providers.sql_database import DataDomain, get_sessionmaker

logger = logging.getLogger(__name__)


def update_document_set(doc_set_uuid, is_new_doc_default=None, is_public_viewable=None, last_user_id=None):
    """
    Update specific fields of a document set record.

    Updates the document set with the provided field values. Only non-None parameters will be
    updated in the database record.
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
    """
    Context manager for updating a document set record in the database.

    Yields the document set record object for modification within a database transaction. Handles
    conversion of string UUIDs and logs warnings for missing or duplicate records.
    """
    if isinstance(doc_set_uuid, str):
        doc_set_uuid = uuid.UUID(hex=doc_set_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        try:
            with session.begin():
                stmt = select(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id == doc_set_uuid)
                result = session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', doc_set_uuid, exc_info=ex)
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', doc_set_uuid, exc_info=ex)
            return

        with session.begin():
            yield existing_obj
