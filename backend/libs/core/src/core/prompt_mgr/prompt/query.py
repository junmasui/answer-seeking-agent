import logging
from typing import Optional

from core_db.db_models import DbAgentPrompt
from core_db.prompt_mgr.prompt.query import list_agent_prompts
from core_public import AgentPrompt, AgentPromptList, AgentPromptStatus, OwnerType

from .stats import get_prompt_statistics

logger = logging.getLogger(__name__)


def list_prompts(
    *,
    name: Optional[str] = None,
    status: Optional[AgentPromptStatus] = None,
    owner_type: Optional[OwnerType] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of prompts."""
    existing_objs = list_agent_prompts(
        name=name, status=status, owner_type=owner_type, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_prompt_statistics()

    def _to_dict(_x: DbAgentPrompt):
        """Convert database agent prompt record to API response AgentPrompt model."""
        return AgentPrompt(
            id=_x.id,
            name=_x.name,
            owner_type=_x.owner_type,
            status=_x.status,
            system_message=_x.system_message,
            human_message=_x.human_message,
            include_history=_x.include_history,
            version=_x.version,
        )

    prompt_list = [_to_dict(x) for x in existing_objs]

    return AgentPromptList(
        prompts=prompt_list, prompt_count=table_stats.prompt_count, table_updated_time=table_stats.table_updated_time
    )


