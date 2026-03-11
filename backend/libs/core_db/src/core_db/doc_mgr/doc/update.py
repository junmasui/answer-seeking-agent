import logging
import uuid
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core_db.db_models import DbTrackedDocument
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_tracking_record(doc_uuid):
    """Updates the tracking record for the document."""
    if isinstance(doc_uuid, str):
        doc_uuid = uuid.UUID(hex=doc_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.AGENT)

    async with sessionmaker() as session:
        async with session.begin():
            stmt = (
                select(DbTrackedDocument)
                .options(selectinload(DbTrackedDocument.chunks))
                .where(DbTrackedDocument.id == doc_uuid)
            )
            result = await session.execute(stmt)

            existing_obj = result.scalar_one_or_none()

            if existing_obj is None:
                logger.warning('No tracking doc record found for %s', doc_uuid)
                yield None
            else:
                yield existing_obj
