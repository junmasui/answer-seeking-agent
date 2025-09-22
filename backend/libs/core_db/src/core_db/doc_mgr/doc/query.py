import logging

from core_db.db_models import DbTrackedDocument
from core_db.db_models.doc_mgr import DbTrackedDocumentSet
from core_db.providers.sql_database import DataDomain, get_sessionmaker
from core_public import DocumentStatus, SortDirection
from sqlalchemy import and_, column, func, select
import uuid
from typing import Optional, Sequence

from sqlalchemy.orm import aliased, subqueryload


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


def list_tracking_records(
    *,
    doc_set_id: Optional[uuid.UUID | list[uuid.UUID]] = None,
    status: Optional[DocumentStatus | list[DocumentStatus]] = None,
    file_name: Optional[str] = None,
    start: Optional[int] = None,
    length: Optional[int] = None,
    sort_by: Optional[list] = None,
    document_set_name: Optional[str] = None,
    content_type: Optional[str] = None,
    source_url: Optional[str] = None,
):
    """
    Return a page of tracking records from the database with filtering and sorting.

    This function constructs and executes a SQL query to fetch document tracking
    records. It supports filtering by various attributes, sorting, and pagination.
    For pagination, it uses a Common Table Expression (CTE) with the ROW_NUMBER()
    window function for performance.

    Args:
        doc_set_id: Optional. A single UUID or a list of UUIDs to filter documents
            by their document set.
        status: Optional. A single DocumentStatus or a list of statuses to filter
            documents by.
        file_name: Optional. A string to filter documents by the start of their
            filename (case-insensitive).
        start: Optional. The starting index for pagination.
        length: Optional. The number of documents to return for pagination.
        sort_by: Optional. A list of tuples for sorting the results.
        document_set_name: Optional. A string to filter documents by the start of
            their document set name (case-insensitive).
        content_type: Optional. A string to filter documents by the start of their
            content type (case-insensitive).
        source_url: Optional. A string to filter documents by the start of their
            source URL (case-insensitive).

    Returns:
        A list of DbTrackedDocument objects.

    """
    order_by = _build_order_by(sort_by)

    sessionmaker = get_sessionmaker(DataDomain.ANSWERS)

    # Determine if we need to explicitly join the related table for sorting inside the
    # primary SQL query. The relationship between SQLAlchemy classes is used only for
    # followup SQL queries to access related data. The explicit join is needed for
    # scenarios that involve WHERE and ORDER BY in the primary SQL query.
    join_document_set = _should_join_document_set(sort_by)

    with sessionmaker() as session:
        paginate = start is not None and length is not None

        core_query = select(DbTrackedDocument)
        if join_document_set:
            # Explicitly join to the related document set table for sorting
            core_query = core_query.join(DbTrackedDocument.document_set)

        # Apply query filters
        where = _build_query_filter(
            doc_set_id,
            status,
            file_name=file_name,
            document_set_name=document_set_name,
            content_type=content_type,
            source_url=source_url,
        )

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
                # Eager load the document set records in a single query.
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
            # Eager load the document set records in a single query.
            query = core_query.options(subqueryload(DbTrackedDocument.document_set))

        result = session.execute(query)
        existing_objs = result.scalars().all()

    return existing_objs

def _should_join_document_set(sort_by):
    """
    Determine if the query should explicitly join the document set table for sorting.

    Args:     sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria.

    Returns:     bool: True if sorting by 'document_set_name', otherwise False.
    """
    join_document_set = False
    if sort_by:
        for field, _ in sort_by:
            if field == 'document_set_name':
                join_document_set = True
                break
    return join_document_set


def _build_query_filter(
    doc_set_id: Optional[uuid.UUID | list[uuid.UUID]],
    status: Optional[DocumentStatus | list[DocumentStatus]],
    *,
    file_name: Optional[str],
    document_set_name: Optional[str],
    content_type: Optional[str],
    source_url: Optional[str],
):
    """
    Build WHERE clause conditions from filter parameters.

    Args:
        doc_set_id: Single document set UUID or list of UUIDs to filter by.
            If None, no document set filtering is applied.
        status: Single DocumentStatus or list of statuses to filter by.
            If None, no status filtering is applied.
        file_name: Filename pattern for istartswith matching (case-insensitive).
            If None, no filename filtering is applied.
        document_set_name: Document set name pattern for istartswith matching
            (case-insensitive). If None, no document set name filtering is applied.
        content_type: Content type pattern for istartswith matching
            (case-insensitive). If None, no content type filtering is applied.
        source_url: Source URL pattern for istartswith matching (case-insensitive).
            If None, no source URL filtering is applied.

    Returns:
        A list of SQLAlchemy WHERE clause conditions that can be used with and_()
        or applied individually to a query.

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
        where.append(DbTrackedDocument.filename.istartswith(file_name))

    if document_set_name is not None:
        where.append(DbTrackedDocumentSet.name.istartswith(document_set_name))

    if content_type is not None:
        where.append(DbTrackedDocument.content_type.istartswith(content_type))

    if source_url is not None:
        where.append(DbTrackedDocument.source_url.istartswith(source_url))

    return where


def _build_order_by(sort_by: Optional[list] = None):
    """
    Build ORDER BY clause expressions from sort specification.

    Args:     sort_by: List or tuple of (field_name, direction) tuples specifying sort criteria. If
    None, defaults to [('name', SortDirection.ASC)].             Supported field names: 'name',
    'size_bytes', 'modification_time',                                    'ingestion_time', 'status'
    Direction should be SortDirection.ASC or SortDirection.DESC

    Returns:     list: List of SQLAlchemy order_by expressions that can be passed to
    query.order_by()

    Raises:     TypeError: If sort_by is not a list or tuple     ValueError: If sort_by is empty or
    contains unknown field names
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
            case 'document_set_name':
                # Sort by related document set's name
                expr = DbTrackedDocumentSet.name
            case 'content_type':
                expr = DbTrackedDocument.content_type
            case 'status':
                expr = DbTrackedDocument.status
            case _:
                raise ValueError('unknown field name', name)
        if expr is None:
            return None
        expr = expr.desc() if direction == SortDirection.DESC else expr.asc()
        return expr

    order_by = [y for x in sort_by if (y := _to_col(x)) is not None]
    return order_by

