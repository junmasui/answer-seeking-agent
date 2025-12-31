import logging
import uuid
from typing import Optional

from core_db.db_models import DbPrompt
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker
from core_public import OwnerType, SortDirection
from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)


async def get_prompt(prompt_uuid_list: list[str | uuid.UUID], owner_type: Optional[OwnerType] = None):
    """Return tracking records when matched to specified prommpt UUID."""

    def _ensure_uuid(item):
        """Convert string to UUID if needed, otherwise return the UUID as-is."""
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    prompt_uuid_list = [_ensure_uuid(item) for item in prompt_uuid_list]

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        where = [DbPrompt.id.in_(prompt_uuid_list)]
        if owner_type is not None:
            where.append(DbPrompt.owner_type == owner_type)

        if len(where) > 1:
            stmt = select(DbPrompt).where(and_(*where))
        elif len(where) == 1:
            stmt = select(DbPrompt).where(where[0])
        else:
            stmt = select(DbPrompt)
        result = await session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def _build_query_filter(name: Optional[str], owner_type: Optional[OwnerType]):
    """
    Build WHERE clause conditions for filtering agent prompts.

    Args:
        name: Optional string to filter prompts by name using case-insensitive matching.
              If provided, uses SQL ILIKE for partial matching.
        owner_type: Optional OwnerType to filter prompts by their owner type.
                   If provided, performs exact equality match.

    Returns:
        list: List of SQLAlchemy WHERE clause conditions that can be combined
              with AND operator for filtering DbAgentPrompt records.
              Returns empty list if no filters are specified.

    """
    where = []
    if name is not None:
        where.append(DbPrompt.name.ilike(name))
    if owner_type is not None:
        where.append(DbPrompt.owner_type == owner_type)
    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:
        sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.
                If None, defaults to [('name', SortDirection.ASC)].
                Supported field names: 'name'
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
        """Convert sort field name and direction to SQLAlchemy column expression."""
        name, direction = x
        expr = None
        match name:
            case 'name':
                expr = DbPrompt.name
            case 'ownerType':
                expr = DbPrompt.owner_type
            case _:
                raise ValueError('unknown field name', name)
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    return_value = [_to_col(x) for x in sort_by]
    return return_value


async def list_prompts(
    *,
    name: Optional[str] = None,
    owner_type: Optional[OwnerType] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return prompts when matched to specified propmt UUID."""
    order_by = _build_order_by(sort_by)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(DbPrompt)

        # Apply query filters
        where = _build_query_filter(name, owner_type)

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
            cte_alias_type = aliased(element=DbPrompt, alias=cte)

            # Query the CTE
            query = select(cte_alias_type).where(
                # NOTE: Use the `column` function to directly reference the CTE column
                #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                #   the model.
                # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                column('row_num').between(start + 1, start + length)
            )
        else:
            query = core_query

        result = await session.execute(query)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs
