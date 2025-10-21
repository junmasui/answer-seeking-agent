import logging
from typing import Optional

from core_db.db_models import DbPromptVersion
from core_db.prompt_mgr.prompt_version.query import list_prompt_versions as db_list_prompt_versions
from core_public import PromptVersion, PromptVersionList
from core_public.prompt_version import PromptStatus

from .stats import get_prompt_version_stats

logger = logging.getLogger(__name__)


def list_prompt_versions(
    *,
    prompt_id: Optional[str] = None,
    status: Optional[PromptStatus] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of prompt versions."""

    existing_objs = db_list_prompt_versions(
        prompt_id=prompt_id, status=status, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_prompt_version_stats()

    def _to_dict(_x: DbPromptVersion):
        """Convert database agent prompt record to API response AgentPrompt model."""
        return PromptVersion(
            id=_x.id,
            prompt_id=_x.prompt_id,
            prompt_name=_x.prompt.name,
            status=_x.status,
            include_history=_x.include_history,
            system_message=_x.system_message,
            human_message=_x.human_message,
            version=_x.version,
        )

    prompt_version_list = [_to_dict(x) for x in existing_objs]

    return PromptVersionList(
        prompt_versions=prompt_version_list,
        prompt_version_count=table_stats.prompt_version_count,
        table_updated_time=table_stats.table_updated_time,
    )
