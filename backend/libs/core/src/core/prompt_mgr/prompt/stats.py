import logging

from core_db.db_models import DbAgentPrompt
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from core_public import AgentPromptStats
from sqlalchemy import func, select

logger = logging.getLogger(__name__)


def get_prompt_statistics():
    """
    Get statistics about the agent prompts table.

    Returns an AgentPromptStats object containing the total count of prompts and the last update
    time from the tracking table.
    """
    table_stats = _get_agent_prompt_stats()

    return AgentPromptStats(prompt_count=table_stats['prompt_count'], table_updated_time=table_stats['max_update_time'])


def _get_agent_prompt_stats():
    """Return the count of records and maximum updated_date time in the prompt table."""
    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(func.count().label('prompt_count'), func.max(DbAgentPrompt.update_time).label('max_update_time'))
        result = session.execute(stmt).first()
    return {'prompt_count': result[0], 'max_update_time': result[1]}
