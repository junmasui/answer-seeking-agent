import logging
from typing import Optional

from core_db.db_models import DbPrompt
from core_db.prompt_mgr.prompt.query import list_prompts as db_list_prompts
from core_public import Prompt, PromptList, OwnerType

from .stats import get_prompt_statistics

logger = logging.getLogger(__name__)


def list_prompts(
    *,
    name: Optional[str] = None,
    owner_type: Optional[OwnerType] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of prompts."""
    existing_objs = db_list_prompts(
        name=name, owner_type=owner_type, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_prompt_statistics()

    def _to_dict(_x: DbPrompt):
        """Convert database agent prompt record to API response AgentPrompt model."""
        return Prompt(
            id=_x.id,
            name=_x.name,
            owner_type=_x.owner_type
        )

    prompt_list = [_to_dict(x) for x in existing_objs]

    return PromptList(
        prompts=prompt_list, prompt_count=table_stats.prompt_count, table_updated_time=table_stats.table_updated_time
    )
