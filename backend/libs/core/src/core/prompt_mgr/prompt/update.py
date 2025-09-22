import logging
from typing import Optional

from core_db.prompt_mgr.prompt.update import update_prompt_record
from core_public import AgentPromptStatus

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


