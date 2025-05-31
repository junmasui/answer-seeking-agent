import logging
import uuid
from typing import Optional, Sequence

from sqlalchemy import and_, column, func, select
from sqlalchemy.orm import aliased, subqueryload

from core.public_models.doc import DocumentStatus

from ...db_models import DbTrackedDocument
from ...providers.sql_database import DataDomain, get_sessionmaker
from ...public_models import Document, DocumentList, SortDirection
from .stats import get_document_statistics

logger = logging.getLogger(__name__)


def get_documents(doc_uuid_list: list[str | uuid.UUID]) -> Sequence[DbTrackedDocument]:
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        """Convert string to UUID if needed, otherwise return the UUID as-is."""
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_uuid_list = [_ensure_uuid(item) for item in doc_uuid_list]

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        stmt = select(DbTrackedDocument).where(DbTrackedDocument.id.in_(doc_uuid_list))
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def list_documents(
    *,
    doc_set_id: Optional[uuid.UUID | list[uuid.UUID]] = None,
    status: Optional[DocumentStatus | list[DocumentStatus]] = None,
    file_name: Optional[str] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """Return the list of files in cloud storage."""
    existing_objs = _list_tracking_records(
        doc_set_id=doc_set_id, status=status, file_name=file_name, start=start, length=length, sort_by=sort_by
    )
    table_stats = get_document_statistics()

    def _to_dict(_x: DbTrackedDocument):
        """Convert database document record to API response Document model."""
        return Document(
            id=_x.id,
            status=_x.status,
            name=_x.filename,
            size_bytes=_x.size_bytes,
            modification_time=_x.file_modified_time.replace(microsecond=0)
            if _x.file_modified_time is not None
            else _x.file_modified_time,
            ingestion_time=_x.ingested_time.replace(microsecond=0)
            if _x.ingested_time is not None
            else _x.ingested_time,
            source_url=_x.source_url,
            content_type=_x.content_type,
            download_time_utc=_x.download_time_utc.replace(second=0, microsecond=0)
            if _x.download_time_utc is not None
            else _x.download_time_utc,
            document_set_id=_x.document_set.id,
            document_set_name=_x.document_set.name,
        )

    file_list = [_to_dict(x) for x in existing_objs]

    return DocumentList(
        documents=file_list,
        document_count=table_stats.document_count,
        table_updated_time=table_stats.table_updated_time,
    )


def _list_tracking_records(
    *,
    doc_set_id: Optional[uuid.UUID | list[uuid.UUID]] = None,
    status: Optional[DocumentStatus | list[DocumentStatus]] = None,
    file_name: Optional[str] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
):
    """
    Return a page of tracking records.

    The implementation is an older known-performance technique. The technique
    creates a CTE (alternatively, a subquery could have been used) where each
    row is augmented with the windowing function ROW_NUMBER. Then the rows whose
    ROW_NUMBER values fall into the page range are choosen. Finally, the row
    data minus the ROW_NUMBER values are returned.
    """
    order_by = _build_order_by(sort_by)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    with sessionmaker() as session:
        paginate = start is not None and length is not None

        core_query = select(DbTrackedDocument)

        # Apply query filters
        where = _build_query_filter(doc_set_id, status, file_name)

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

            # Create a CTE from the query.
            cte = cte_query.cte(name='row_numbered')

            # Alias the CTE
            WindowedTrackedDocument = aliased(element=DbTrackedDocument, alias=cte)

            # Query the CTE
            query = (
                select(WindowedTrackedDocument)
                .options(subqueryload(WindowedTrackedDocument.document_set))
                .where(
                    # NOTE: Use the `column` function to directly reference the CTE column
                    #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                    #   the model.
                    # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                    column('row_num').between(start + 1, start + length)
                )
            )
        else:
            query = core_query.options(subqueryload(DbTrackedDocument.document_set))

        result = session.execute(query)
        existing_objs = result.scalars().all()

    return existing_objs


def _build_query_filter(
    doc_set_id: Optional[uuid.UUID | list[uuid.UUID]],
    status: Optional[DocumentStatus | list[DocumentStatus]],
    file_name: Optional[str],
):
    """
    Build WHERE clause conditions from filter parameters.

    Args:
        doc_set_id: Single document set UUID or list of UUIDs to filter by.
                   If None, no document set filtering is applied.
        status: Single DocumentStatus or list of statuses to filter by.
               If None, no status filtering is applied.
        file_name: Filename pattern for ILIKE matching (case-insensitive).
                  If None, no filename filtering is applied.

    Returns:
        list: List of SQLAlchemy WHERE clause conditions that can be used
              with and_() or applied individually to a query.
    """
    where = []
    if doc_set_id is not None:
        if isinstance(doc_set_id, list):
            where.append(DbTrackedDocument.document_set_id.in_(doc_set_id))
        elif isinstance(doc_set_id, uuid.UUID):
            where.append(DbTrackedDocument.document_set_id == doc_set_id)
    if status is not None:
        if isinstance(status, list):
            if len(status) > 0:
                where.append(DbTrackedDocument.status.in_(status))
        elif isinstance(status, DocumentStatus):
            where.append(DbTrackedDocument.status == status)

    if file_name is not None:
        where.append(DbTrackedDocument.filename.ilike(file_name))
    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:
        sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.
                If None, defaults to [('name', SortDirection.ASC)].
                Supported field names: 'name', 'size_bytes', 'modification_time', 'ingestion_time', 'status'
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
                expr = DbTrackedDocument.filename
            case 'size_bytes':
                expr = DbTrackedDocument.size_bytes
            case 'modification_time':
                expr = DbTrackedDocument.file_modified_time
            case 'ingestion_time':
                expr = DbTrackedDocument.ingested_time
            case 'status':
                expr = DbTrackedDocument.status
            case _:
                raise ValueError('unknown field name', name)
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    order_by = [_to_col(x) for x in sort_by]
    return order_by
