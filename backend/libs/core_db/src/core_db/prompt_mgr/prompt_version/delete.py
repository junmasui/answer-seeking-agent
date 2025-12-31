import logging
import uuid

from sqlalchemy import delete

from core_db.db_models import DbPromptVersion
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


async def delete_prompt_version(prompt_version_uuid):
    """Deletes the prompt version record."""
    if isinstance(prompt_version_uuid, str):
        prompt_version_uuid = uuid.UUID(hex=prompt_version_uuid)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session, session.begin():
        stmt = delete(DbPromptVersion).where(DbPromptVersion.id == prompt_version_uuid)
        result = await session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No prompt version found with UUID %s', prompt_version_uuid)
    else:
        logger.debug('Successfully deleted prompt version with UUID %s', prompt_version_uuid)
