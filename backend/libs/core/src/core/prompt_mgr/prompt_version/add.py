import logging
import uuid
from typing import Optional

from core_db.prompt_mgr.prompt_version.add import add_or_update_prompt_version
from core_public import OwnerType, PromptStatus

logger = logging.getLogger(__name__)


def add_prompt_version(
    prompt_id: uuid.UUID,
    status: PromptStatus,
    include_history: bool | None,
    system_message: str,
    human_message: str,
    user_id: Optional[str] = None,
):
    """Add a new prompt version."""
    return add_or_update_prompt_version(
        prompt_id=prompt_id,
        status=status,
        include_history=include_history,
        system_message=system_message,
        human_message=human_message,
        user_id=user_id,
    )
