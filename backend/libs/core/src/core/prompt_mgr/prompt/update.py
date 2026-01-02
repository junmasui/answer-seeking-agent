import logging

from core_db.prompt_mgr.prompt.update import update_prompt_record

logger = logging.getLogger(__name__)


async def update_prompt(prompt_uuid, last_user_id=None):
    """Updates status field with option to update."""
    async with update_prompt_record(prompt_uuid=prompt_uuid) as record:
        if last_user_id:
            record.last_user_id = last_user_id
