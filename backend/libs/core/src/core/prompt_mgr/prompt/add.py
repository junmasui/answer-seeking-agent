import logging
import uuid

from core_db.prompt_mgr.prompt.add import add_or_update_prompt
from core_public import OwnerType

logger = logging.getLogger(__name__)


def add_prompt(
    name: str,
    owner_type: OwnerType,
    user_id: uuid.UUID = None,
):
    """
    Add a new agent prompt with the specified configuration.

    Creates a new prompt entry with automatic version incrementing. If the status is ACTIVE,
    deactivates all other versions of the same prompt name.
    """
    return add_or_update_prompt(
        name=name,
        owner_type=owner_type,
        user_id=user_id,
    )
