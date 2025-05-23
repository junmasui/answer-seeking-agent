import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import DbTrackedDocument


logger = logging.getLogger(__name__)


def update_document_status(doc_uuid, status, last_user_id=None):
    """Updates status field with option to update"""
    with update_tracking_record(doc_uuid=doc_uuid) as record:
        if record is None:
            return

        record.status = status
        if last_user_id:
            record.last_user_id = last_user_id


def update_document(doc_uuid, doc_set_uuid=None, last_user_id=None):
    """Updates status field with option to update"""
    with update_tracking_record(doc_uuid=doc_uuid) as record:
        if record is None:
            return

        if doc_set_uuid is not None:
            record.document_set_id = doc_set_uuid

        if last_user_id:
            record.last_user_id = last_user_id


@contextmanager
def update_tracking_record(doc_uuid):
    """Updates the tracking record for the document."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        try:
            with session.begin():
                stmt = select(DbTrackedDocument).where(DbTrackedDocument.id == doc_uuid)
                result = session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', doc_uuid, exc_info=ex)
            yield None
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', doc_uuid, exc_info=ex)
            yield None
            return

        with session.begin():
            yield existing_obj
