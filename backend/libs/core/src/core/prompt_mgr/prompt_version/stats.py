import logging

from core_db.prompt_mgr.prompt_version.stats import get_prompt_version_stats as db_get_prompt_version_stats
from core_public import PromptVersionStats

logger = logging.getLogger(__name__)


def get_prompt_version_stats():
    """Return statistics about the prompt versions."""
    table_stats = db_get_prompt_version_stats()
    return PromptVersionStats(
        prompt_version_count=table_stats['prompt_version_count'],
        table_updated_time=table_stats['max_update_time'],
    )
