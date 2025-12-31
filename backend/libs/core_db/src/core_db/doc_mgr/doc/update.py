import logging
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_tracking_record(doc_uuid):
    """Updates the tracking record for the document."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        try:
            async with session.begin():
                stmt = select(DbTrackedDocument).where(DbTrackedDocument.id == doc_uuid)
                result = await session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', doc_uuid, exc_info=ex)
            yield None
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', doc_uuid, exc_info=ex)
            yield None
            return

        async with session.begin():
            yield existing_obj
