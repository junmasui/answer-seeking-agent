import logging
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from core_db.db_models import DbTrackedDocumentSet
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_doc_set_record(doc_set_uuid):
    """
    Context manager for updating a document set record in the database.

    Yields the document set record object for modification within a database transaction. Handles
    conversion of string UUIDs and logs warnings for missing or duplicate records.
    """
    if isinstance(doc_set_uuid, str):
        doc_set_uuid = uuid.UUID(hex=doc_set_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.AGENT)

    async with sessionmaker() as session:
        async with session.begin():
            try:
                stmt = select(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id == doc_set_uuid)
                result = await session.execute(stmt)

                existing_obj = result.scalar_one()

            except NoResultFound as ex:
                logger.warning('No tracking doc record found for %s', doc_set_uuid, exc_info=ex)
                return
            except MultipleResultsFound as ex:
                logger.warning('Multiple tracking doc records found for %s', doc_set_uuid, exc_info=ex)
                return

            yield existing_obj
