import logging
import uuid
from typing import Optional

from core_public import SortDirection
from core_public.prompt_version import PromptStatus
from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased, selectinload

from core_db.db_models import DbPrompt, DbPromptVersion
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker

logger = logging.getLogger(__name__)


async def get_prompt_version(prompt_version_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified prommpt version UUID."""

    def _ensure_uuid(item):
        """Convert string to UUID if needed, otherwise return the UUID as-is."""
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    prompt_version_uuid_list = [_ensure_uuid(item) for item in prompt_version_uuid_list]

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        where = [DbPromptVersion.id.in_(prompt_version_uuid_list)]

        if len(where) > 1:
            stmt = select(DbPromptVersion).where(and_(*where))
        elif len(where) == 1:
            stmt = select(DbPromptVersion).where(where[0])
        else:
            stmt = select(DbPromptVersion)
        result = await session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def _build_query_filter(prompt_id: uuid.UUID, status: PromptStatus):
    """Build WHERE clause conditions for filtering agent prompts."""
    where = []
    if prompt_id is not None:
        where.append(DbPromptVersion.prompt_id == prompt_id)
    if status is not None:
        where.append(DbPromptVersion.status == status)
    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:
        sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.
                If None, defaults to [('version', SortDirection.ASC)].
                Supported field names: 'version'
                Direction should be SortDirection.ASC or SortDirection.DESC

    Returns:
        list: List of SQLAlchemy order_by expressions that can be passed to query.order_by()

    Raises:
        TypeError: If sort_by is not a list or tuple
        ValueError: If sort_by is empty or contains unknown field names

    """
    if sort_by is None:
        sort_by = [('version', SortDirection.ASC)]
    elif not isinstance(sort_by, (list, tuple)):
        raise TypeError('sort_by must be a list or tuple')
    elif len(sort_by) == 0:
        raise ValueError('sort_by cannot be empty')

    def _to_col(x):
        """Convert sort field name and direction to SQLAlchemy column expression."""
        name, direction = x
        expr = None
        match name:
            case 'version':
                expr = DbPromptVersion.version
            case _:
                raise ValueError('unknown field name', name)
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    return_value = [_to_col(x) for x in sort_by]
    return return_value


async def list_prompt_versions(
    *,
    prompt_id: Optional[uuid.UUID] = None,
    status: Optional[PromptStatus] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return prompts when matched to specified propmt UUID."""
    order_by = _build_order_by(sort_by)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    join_prompt = True

    async with sessionmaker() as session:
        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(DbPromptVersion)
        if join_prompt:
            # Explicitly join to the related prompt table for sorting
            core_query = core_query.join(DbPrompt)

        # Apply query filters
        where = _build_query_filter(prompt_id, status)

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
            cte_alias_type = aliased(element=DbPromptVersion, alias=cte)

            # Query the CTE
            query = (
                select(cte_alias_type)
                # Eager load the parent prompt records in a single 2nd query.
                # The parent records are loaded using a WHERE IN clause using
                # the results of the 1st query.
                .options(selectinload(cte_alias_type.prompt))
                .where(
                    # NOTE: Use the `column` function to directly reference the CTE column
                    #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                    #   the model.
                    # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                    column('row_num').between(start + 1, start + length)
                )
            )
        else:
            # Eager load the parent prompt records in a single 2nd query.
            # The parent records are loaded using a WHERE IN clause using
            # the results of the 1st query.
            query = core_query.options(selectinload(DbPromptVersion.prompt))

        result = await session.execute(query)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs
