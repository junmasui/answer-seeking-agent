import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased

from ...db_models import DbTrackedDocumentSet
from ...providers.sql_database import DataDomain, get_sessionmaker
from ...public_models import DocumentSet, DocumentSetList, DocumentSetStatus, SortDirection
from .stats import get_document_set_statistics

logger = logging.getLogger(__name__)


def get_document_sets(doc_set_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_set_uuid_list = [_ensure_uuid(item) for item in doc_set_uuid_list]

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(DbTrackedDocumentSet).where(DbTrackedDocumentSet.id.in_(doc_set_uuid_list))
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def list_document_sets(
    *,
    name: Optional[str] = None,
    is_default: Optional[bool] = None,
    is_public: Optional[bool] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of document sets."""

    existing_objs = _list_tracking_document_sets(
        name=name, is_default=is_default, is_public=is_public, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_document_set_statistics()

    def _to_dict(_x: DbTrackedDocumentSet):
        return DocumentSet(
            id=_x.id,
            name=_x.name,
            status=DocumentSetStatus.ACTIVE,  # TODO - Replace hardcode with database column
            is_new_doc_default=_x.is_new_doc_default,
            is_public_viewable=_x.is_public_viewable,
        )

    doc_set_list = [_to_dict(x) for x in existing_objs]

    return DocumentSetList(
        document_sets=doc_set_list,
        document_set_count=table_stats.document_set_count,
        table_updated_time=table_stats.table_updated_time,
    )


def _list_tracking_document_sets(
    *,
    name: Optional[str] = None,
    is_default: Optional[bool] = None,
    is_public: Optional[bool] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return tracking set when matched to specified document UUID."""

    if sort_by is None:
        sort_by = [('name', SortDirection.ASC)]
    elif not isinstance(sort_by, (list, tuple)):
        raise TypeError('sort_by must be a list or tuple')
    elif len(sort_by) == 0:
        raise ValueError('sort_by cannot be empty')

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    def _to_col(x):
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

    with sessionmaker() as session:
        paginate = start is not None and length is not None

        # When paginating, we add a windowing function to the selected fields.
        core_query = select(DbTrackedDocumentSet)

        # Apply query filters
        where = []
        if name is not None:
            where.append(DbTrackedDocumentSet.name.ilike(name))
        if is_default is not None:
            where.append(DbTrackedDocumentSet.is_new_doc_default == is_default)
        if is_public is not None:
            where.append(DbTrackedDocumentSet.is_public_viewable == is_public)

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
            WindowedTrackedDocumentSet = aliased(element=DbTrackedDocumentSet, alias=cte)

            # Query the CTE
            query = select(WindowedTrackedDocumentSet).where(
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
