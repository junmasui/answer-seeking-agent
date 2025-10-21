import logging
import uuid
from contextlib import contextmanager

from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

logger = logging.getLogger(__name__)


@contextmanager
def update_prompt_record(prompt_uuid):
    """Updates the prompt record."""
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        try:
            with session.begin():
                stmt = select(DbPrompt).where(DbPrompt.id == prompt_uuid)
                result = session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', prompt_uuid, exc_info=ex)
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', prompt_uuid, exc_info=ex)
            return

        with session.begin():
            yield existing_obj
