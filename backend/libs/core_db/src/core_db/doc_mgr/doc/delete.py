import logging
import uuid

from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker
from sqlalchemy import delete

logger = logging.getLogger(__name__)


async def delete_tracking_record(doc_uuid):
    """Deletes the tracking record."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session, session.begin():
        stmt = delete(DbTrackedDocument).where(DbTrackedDocument.id == doc_uuid)
        result = await session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No tracking record found with UUID %s', doc_uuid)
    else:
        logger.debug('Successfully deleted tracking record with UUID %s', doc_uuid)
