import logging

from core_db.prompt_mgr.prompt.delete import delete_agent_prompt
from core_db.prompt_mgr.prompt.query import get_prompt

logger = logging.getLogger(__name__)


def delete_prompt(prompt_uuid):
    """Delete prompt."""
    # Retrieve prompt record.

    prompt_records = get_prompt(prompt_uuid_list=[prompt_uuid])
    if not prompt_records:
        return False

    prompt_record = prompt_records[0]

    # Delete prompt record.

    delete_agent_prompt(prompt_record.id)

    return True
