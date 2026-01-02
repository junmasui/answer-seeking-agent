import logging
import uuid

from sqlalchemy import delete

from core_db.db_models import DbTrackedDocumentSet
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


async def delete_tracking_record(doc_set_uuid):
    """Deletes the tracking record."""
    if isinstance(doc_set_uuid, str):
        doc_set_uuid = uuid.UUID(hex=doc_set_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session, session.begin():
        stmt = delete(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id == doc_set_uuid)
        result = await session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No document set found with UUID %s', doc_set_uuid)
    else:
        logger.debug('Successfully deleted document set with UUID %s', doc_set_uuid)
