import logging

from core_db.prompt_mgr.prompt.stats import get_agent_prompt_stats
from core_public import AgentPromptStats

logger = logging.getLogger(__name__)


def get_prompt_statistics():
    """
    Get statistics about the agent prompts table.

    Returns an AgentPromptStats object containing the total count of prompts and the last update
    time from the tracking table.
    """
    table_stats = get_agent_prompt_stats()

    return AgentPromptStats(prompt_count=table_stats['prompt_count'], table_updated_time=table_stats['max_update_time'])


