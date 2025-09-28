import logging
import uuid

from core_db.prompt_mgr.prompt.add import add_or_update_agent_prompt
from core_public import AgentPromptStatus, OwnerType

logger = logging.getLogger(__name__)


def add_prompt(
    name: str,
    owner_type: OwnerType,
    status: AgentPromptStatus,
    system_message: str | None,
    human_message: str | None,
    include_history: bool | None,
    user_id: uuid.UUID = None,
):
    """
    Add a new agent prompt with the specified configuration.

    Creates a new prompt entry with automatic version incrementing. If the status is ACTIVE,
    deactivates all other versions of the same prompt name.
    """
    add_or_update_agent_prompt(
        name=name,
        owner_type=owner_type,
        status=status,
        system_message=system_message,
        human_message=human_message,
        include_history=include_history,
        user_id=user_id,
    )
