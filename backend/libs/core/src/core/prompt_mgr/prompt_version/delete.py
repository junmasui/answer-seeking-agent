import logging
import uuid

from core_db.prompt_mgr.prompt_version.delete import delete_prompt_version as db_delete_prompt_version

logger = logging.getLogger(__name__)


async def delete_prompt_version(prompt_version_id: uuid.UUID):
    """Delete a prompt version."""
    return await db_delete_prompt_version(prompt_version_id)
