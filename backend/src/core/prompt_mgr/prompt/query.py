import logging
import uuid
from typing import Optional

from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased

from ...db_models import DbAgentPrompt
from ...providers.sql_database import DataDomain, get_sessionmaker
from ...public_models import AgentPrompt, AgentPromptList, AgentPromptStatus, SortDirection
from ...public_models.base import OwnerType
from .stats import get_prompt_statistics

logger = logging.getLogger(__name__)


def get_prompt(prompt_uuid_list: list[str | uuid.UUID], status: Optional[AgentPromptStatus] = AgentPromptStatus.ACTIVE):
    """Return tracking records when matched to specified prommpt UUID."""

    def _ensure_uuid(item):
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    prompt_uuid_list = [_ensure_uuid(item) for item in prompt_uuid_list]

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        where = [DbAgentPrompt.id.in_(prompt_uuid_list)]
        if status is not None:
            where.append(DbAgentPrompt.status == status)

        if len(where) > 1:
            stmt = select(DbAgentPrompt).where(and_(*where))
        elif len(where) == 1:
            stmt = select(DbAgentPrompt).where(where[0])
        else:
            stmt = select(DbAgentPrompt)
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


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
    existing_objs = _list_agent_prompts(
        name=name, status=status, owner_type=owner_type, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_prompt_statistics()

    def _to_dict(_x: DbAgentPrompt):
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


def _list_agent_prompts(
    *,
    name: Optional[str] = None,
    status: Optional[AgentPromptStatus] = None,
    owner_type: Optional[OwnerType] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return prompts when matched to specified propmt UUID."""
    order_by = _build_order_by(sort_by)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(DbAgentPrompt)

        # Apply query filters
        where = _build_query_filter(name, status, owner_type)

        if len(where) > 1:
            core_query = core_query.where(and_(*where))
        elif len(where) == 1:
            core_query = core_query.where(where[0])

        # Apply sorting
        core_query = core_query.order_by(*order_by)

        # Apply pagination if requested
        if paginate:
            # When paginating, we add a windowing function to the selected fields.
            cte_query = core_query.add_columns(func.row_number().over(order_by=order_by).label('row_num'))

            # Create a CTE from the core query.
            cte = cte_query.cte(name='row_numbered')

            # Alias the CTE
            WindowedAgentPrompt = aliased(element=DbAgentPrompt, alias=cte)

            # Query the CTE
            query = select(WindowedAgentPrompt).where(
                # NOTE: Use the `column` function to directly reference the CTE column
                #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                #   the model.
                # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                column('row_num').between(start + 1, start + length)
            )
        else:
            query = core_query

        result = session.execute(query)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def _build_query_filter(name: Optional[str], status: Optional[AgentPromptStatus], owner_type: Optional[OwnerType]):
    """
    Build WHERE clause conditions for filtering agent prompts.

    Args:
        name: Optional string to filter prompts by name using case-insensitive matching.
              If provided, uses SQL ILIKE for partial matching.
        status: Optional AgentPromptStatus to filter prompts by their current status.
                If provided, performs exact equality match.
        owner_type: Optional OwnerType to filter prompts by their owner type.
                   If provided, performs exact equality match.

    Returns:
        list: List of SQLAlchemy WHERE clause conditions that can be combined
              with AND operator for filtering DbAgentPrompt records.
              Returns empty list if no filters are specified.
    """
    where = []
    if name is not None:
        where.append(DbAgentPrompt.name.ilike(name))
    if status is not None:
        where.append(DbAgentPrompt.status == status)
    if owner_type is not None:
        where.append(DbAgentPrompt.owner_type == owner_type)
    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:
        sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.
                If None, defaults to [('name', SortDirection.ASC)].
                Supported field names: 'name', 'status'
                Direction should be SortDirection.ASC or SortDirection.DESC

    Returns:
        list: List of SQLAlchemy order_by expressions that can be passed to query.order_by()

    Raises:
        TypeError: If sort_by is not a list or tuple
        ValueError: If sort_by is empty or contains unknown field names
    """
    if sort_by is None:
        sort_by = [('name', SortDirection.ASC)]
    elif not isinstance(sort_by, (list, tuple)):
        raise TypeError('sort_by must be a list or tuple')
    elif len(sort_by) == 0:
        raise ValueError('sort_by cannot be empty')

    def _to_col(x):
        name, direction = x
        expr = None
        match name:
            case 'name':
                expr = DbAgentPrompt.name
            case 'status':
                expr = DbAgentPrompt.status
            case _:
                raise ValueError('unknown field name', name)
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    return_value = [_to_col(x) for x in sort_by]
    return return_value
