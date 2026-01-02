import logging

from core_db.prompt_mgr.prompt.delete import delete_prompt as db_delete_prompt
from core_db.prompt_mgr.prompt.query import get_prompt

logger = logging.getLogger(__name__)


async def delete_prompt(prompt_uuid):
    """Delete prompt."""
    # Retrieve prompt record.

    prompt_records = await get_prompt(prompt_uuid_list=[prompt_uuid])
    if not prompt_records:
        return False

    prompt_record = prompt_records[0]

    # Delete prompt record.

    await db_delete_prompt(prompt_record.id)

    return True
