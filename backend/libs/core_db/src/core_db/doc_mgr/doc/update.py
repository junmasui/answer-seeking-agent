import logging
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.orm import undefer

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
        async with session.begin():
            # Fix for MissingGreenlet error during attribute access.
            #
            # * Expectation: `select(DbTrackedDocument)` eagerly loads all columns.
            # * Reality: The `vector_ids` column (MutableList of ARRAY) was being deferred or considered expired,
            #   causing a lazy load upon access.
            #
            # The visible `MissingGreenlet` error is caused by SQLAlchemy attempting to perform a synchronous
            # lazy load (and potentially an autoflush) when `vector_ids` is accessed. This fails because
            # the operation is running in an async session without the necessary greenlet context.
            # Adding `undefer` forces the column to be loaded immediately in the initial query, avoiding
            # the lazy load and the resulting error.
            stmt = (
                select(DbTrackedDocument)
                .options(undefer(DbTrackedDocument.vector_ids))
                .where(DbTrackedDocument.id == doc_uuid)
            )
            result = await session.execute(stmt)

            existing_obj = result.scalar_one_or_none()

            if existing_obj is None:
                logger.warning('No tracking doc record found for %s', doc_uuid)
                yield None
            else:
                yield existing_obj
