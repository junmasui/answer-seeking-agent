import logging
from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from sqlalchemy import delete


import uuid
logger = logging.getLogger(__name__)


def delete_tracking_record(doc_uuid):
    """Deletes the tracking record."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session, session.begin():
        stmt = delete(DbTrackedDocument).where(DbTrackedDocument.id == doc_uuid)
        result = session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No tracking record found with UUID %s', doc_uuid)
    else:
        logger.debug('Successfully deleted tracking record with UUID %s', doc_uuid)