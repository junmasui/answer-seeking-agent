import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from core.public_models.prompt import AgentPromptStatus

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import DbAgentPrompt


logger = logging.getLogger(__name__)

def update_prompt(prompt_uuid, status: AgentPromptStatus, system_message: str = None, human_message:str = None, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_prompt_record(prompt_uuid=prompt_uuid) as record:

        if status is not None:
            record.status = status

        if system_message is not None:
            record.system_message = system_message

        if human_message is not None:
            record.human_message = human_message

        if last_user_id:
            record.last_user_id = last_user_id



@contextmanager
def update_prompt_record(prompt_uuid):
    """Updates the prompt record.
    """
    if isinstance(prompt_uuid, str):
        prompt_uuid = uuid.UUID(hex=prompt_uuid)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:

        try:
            with session.begin():
                stmt = select(DbAgentPrompt).where(
                    DbAgentPrompt.id == prompt_uuid)
                result = session.execute(stmt)

                existing_obj = result.scalar_one()

        except NoResultFound as ex:
            logger.warning('No tracking doc record found for %s', doc_uuid, exc_info=ex)
            return
        except MultipleResultsFound as ex:
            logger.warning('Multiple tracking doc records found for %s', doc_uuid, exc_info=ex)
            return

        with session.begin():
            yield existing_obj

            # IMPORTANT!!
            # We should always access SQLAlchemy object properties inside a transaction. Its ORM
            # has subtle lazy-loading behaviors, including when expire_on_commit=True (which is important
            # for data consistency checking). Doing this will prevent auto-transactions from
            # interferring with the next transaction.
            status = existing_obj.status
            name = existing_obj.name
            version = existing_obj.version

        # Count versions. The count will be the number of records with this prompt's name.
        with session.begin():
            stmt = select(func.count()).select_from(DbAgentPrompt).where(
                DbAgentPrompt.name == name)
            result = session.execute(stmt)
            version_count = result.scalar()
        
        # Only one version can be active
        if status == AgentPromptStatus.ACTIVE and version_count > 1:
            with session.begin():
                stmt = update(DbAgentPrompt).where(
                        and_(DbAgentPrompt.name == name, DbAgentPrompt.version != version)
                    ).value(
                        status = AgentPromptStatus.INACTIVE
                    )
                result = session.execute(stmt)
