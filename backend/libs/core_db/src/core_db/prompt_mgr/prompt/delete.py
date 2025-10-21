import logging
import uuid

from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from sqlalchemy import delete

logger = logging.getLogger(__name__)


def delete_prompt(prompt_uuid):
    """Deletes the prompt record."""
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session, session.begin():
        stmt = delete(DbPrompt).where(DbPrompt.id == prompt_uuid)
        result = session.execute(stmt)

    if result.rowcount == 0:
        logger.warning('No prompt found with UUID %s', prompt_uuid)
    else:
        logger.debug('Successfully deleted prompt with UUID %s', prompt_uuid)
