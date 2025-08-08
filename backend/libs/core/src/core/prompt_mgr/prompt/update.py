import logging
import uuid
from contextlib import contextmanager
from typing import Optional

from core_db.db_models import DbAgentPrompt
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from core_public import AgentPromptStatus
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

logger = logging.getLogger(__name__)


def update_prompt(
    prompt_uuid,
    status: Optional[AgentPromptStatus] = None,
    system_message: Optional[str] = None,
    human_message: Optional[str] = None,
    include_history: Optional[bool] = None,
    last_user_id=None,
):
    """Updates status field with option to update."""
    with update_prompt_record(prompt_uuid=prompt_uuid) as record:
        if status is not None:
            record.status = status

        if system_message is not None:
            record.system_message = system_message

        if human_message is not None:
            record.human_message = human_message

        if include_history is not None:
            record.include_history = include_history

        if last_user_id:
            record.last_user_id = last_user_id


@contextmanager
def update_prompt_record(prompt_uuid):
    """Updates the prompt record."""
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        try:
            with session.begin():
                stmt = select(DbAgentPrompt).where(DbAgentPrompt.id == prompt_uuid)
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

            # IMPORTANT!!
            # We should always access SQLAlchemy object properties inside a transaction. Its ORM
            # has subtle lazy-loading behaviors, including when expire_on_commit=True (which is
            # important for data consistency checking). Doing this will prevent auto-transactions
            # from interferring with the next transaction.
            status = existing_obj.status
            name = existing_obj.name
            version = existing_obj.version

        # Count versions. The count will be the number of records with this prompt's name.
        with session.begin():
            stmt = select(func.count()).select_from(DbAgentPrompt).where(DbAgentPrompt.name == name)
            result = session.execute(stmt)
            version_count = result.scalar()

        # Only one version can be active
        if status == AgentPromptStatus.ACTIVE and version_count > 1:
            with session.begin():
                stmt = (
                    update(DbAgentPrompt)
                    .where(and_(DbAgentPrompt.name == name, DbAgentPrompt.version != version))
                    .value(status=AgentPromptStatus.INACTIVE)
                )
                result = session.execute(stmt)
