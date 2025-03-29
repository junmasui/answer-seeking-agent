import logging
import uuid
from contextlib import contextmanager

from sqlalchemy import select

from core.public_models.prompt import AgentPromptStatus

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import AgentPrompt


logger = logging.getLogger(__name__)

def update_prompt(prompt_uuid, status: AgentPromptStatus, system_prompt: str = None, human_prompt:str = None, last_user_id=None):
    """Updates status field with option to update 
    """
    with update_prompt_record(prompt_uuid=prompt_uuid) as record:

        if status is not None:
            record.status = status

        if system_prompt is not None:
            record.system_prompt = system_prompt

        if human_prompt is not None:
            record.human_prompt = human_prompt

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

        with session.begin():
            stmt = select(AgentPrompt).where(
                AgentPrompt.id == prompt_uuid)
            result = session.execute(stmt)
            existing_obj = result.scalar_one()

        with session.begin():
            yield existing_obj

