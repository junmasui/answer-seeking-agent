import logging
import uuid
from typing import Optional

from core_db.db_models import DbTrackedDocumentSet
from core_db.providers.sql_database import DataDomain, get_async_sessionmaker
from core_public import SortDirection
from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased

logger = logging.getLogger(__name__)


async def get_document_sets(doc_set_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        """Convert string to UUID if needed, otherwise return the UUID as-is."""
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_set_uuid_list = [_ensure_uuid(item) for item in doc_set_uuid_list]

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        stmt = select(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id.in_(doc_set_uuid_list))
        result = await session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


async def list_tracking_document_sets(
    *,
    name: Optional[str] = None,
    is_default: Optional[bool] = None,
    is_public: Optional[bool] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return tracking set when matched to specified document UUID."""
    order_by = _build_order_by(sort_by)

    sessionmaker = get_async_sessionmaker(DataDomain.ANSWERS)

    async with sessionmaker() as session:
        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(DbTrackedDocumentSet)

        # Apply query filters
        where = _build_query_filter(name, is_default, is_public)

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
            cte_alias_type = aliased(element=DbTrackedDocumentSet, alias=cte)

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


def _build_query_filter(
    name: Optional[str] = None, is_default: Optional[bool] = None, is_public: Optional[bool] = None
):
    """
    Build WHERE clause conditions for filtering document sets.

    Args:
        name: Optional string to filter by document set name using case-insensitive LIKE matching.
              If provided, filters for document sets whose name contains this string.
        is_default: Optional boolean to filter by whether the document set is the default
                   for new documents. If True, returns only default sets; if False, returns
                   only non-default sets; if None, no filtering is applied.
        is_public: Optional boolean to filter by whether the document set is publicly viewable.
                  If True, returns only public sets; if False, returns only private sets;
                  if None, no filtering is applied.

    Returns:
        list: List of SQLAlchemy WHERE clause expressions that can be applied to a query.
              Returns an empty list if no filters are specified.

    """
    where = []
    if name is not None:
        where.append(DbTrackedDocumentSet.name.ilike(name))
    if is_default is not None:
        where.append(DbTrackedDocumentSet.is_new_doc_default == is_default)
    if is_public is not None:
        where.append(DbTrackedDocumentSet.is_public_viewable == is_public)
    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:
        sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.
                If None, defaults to [('name', SortDirection.ASC)].
                Supported field names: 'name', 'is_new_doc_default', 'is_public_viewable'
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
                expr = DbTrackedDocumentSet.name
            case 'is_new_doc_default':
                expr = DbTrackedDocumentSet.is_new_doc_default
            case 'is_public_viewable':
                expr = DbTrackedDocumentSet.is_public_viewable
            case _:
                raise ValueError('unknown field name', name)
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    order_by = [_to_col(x) for x in sort_by]
    return order_by
