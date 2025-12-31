import logging
import uuid
from contextlib import asynccontextmanager

from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

logger = logging.getLogger(__name__)


@asynccontextmanager
async def update_prompt_record(prompt_uuid):
    """Updates the prompt record."""
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        try:
            async with session.begin():
                stmt = select(DbPrompt).where(DbPrompt.id == prompt_uuid)
                result = await session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', prompt_uuid, exc_info=ex)
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', prompt_uuid, exc_info=ex)
            return

        async with session.begin():
            yield existing_obj
