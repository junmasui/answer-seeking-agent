import logging
import uuid

from sqlalchemy import select

from core.public_models.prompt import AgentPromptStatus
from global_config import get_global_config

from ...providers.sql_database import get_sessionmaker, DataDomain

from ...db_models import AgentPrompt


logger = logging.getLogger(__name__)


def add_prompt(name: str, status: AgentPromptStatus, system_message: str, human_message:str, user_id: uuid.UUID=None):

    _add_or_update_agent_prompt(name=name, status=status, system_message=system_message, human_message=human_message, user_id=user_id)


def _add_or_update_agent_prompt(name: str, status: AgentPromptStatus, system_message: str, human_message:str, user_id: uuid.UUID):
    """Adds or updates the prompt.
    """

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        with session.begin():
            stmt = select(AgentPrompt).where(
                AgentPrompt.name == name)
            result = session.execute(stmt)
            existing_obj = result.scalar_one_or_none()

        with session.begin():
            if existing_obj:
                existing_obj.name = name
                existing_obj.status = status
                existing_obj.system_message = system_message
                existing_obj.human_message = human_message
                if user_id is not None:
                    existing_obj.last_user_id = user_id
            else:
                prompt_uuid = uuid.uuid4()

                new_obj = AgentPrompt(
                    id=prompt_uuid,
                    name=name,
                    status=status,
                    system_message=system_message,
                    human_message=human_message,
                    version=1, # First version!
                    last_user_id=user_id
                )
                session.add(new_obj)
