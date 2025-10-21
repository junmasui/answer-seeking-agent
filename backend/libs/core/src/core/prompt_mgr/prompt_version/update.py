import logging
import uuid
from typing import Optional

from core_db.prompt_mgr.prompt_version.update import update_prompt_version_record
from core_public import PromptStatus

logger = logging.getLogger(__name__)


def update_prompt_version(
    prompt_id: uuid.UUID,
    prompt_version_id: Optional[uuid.UUID] = None,
    version: Optional[int] = None,
    status: Optional[PromptStatus] = None,
    include_history: Optional[bool] = None,
    system_message: Optional[str] = None,
    human_message: Optional[str] = None,
    last_user_id: Optional[str] = None,
):
    """Update a prompt version."""

    # TODO:
    # Add new version if message is changed.
    # Update version if only status is changed

    with update_prompt_version_record(prompt_uuid=prompt_id, prompt_version_uuid=prompt_version_id) as record:
        if status is not None:
            record.status = status

        if include_history is not None:
            record.include_history = include_history

        if system_message is not None:
            record.system_message = system_message

        if human_message is not None:
            record.human_message = human_message

        if last_user_id:
            record.last_user_id = last_user_id
