import logging
from typing import Optional
import uuid

from sqlalchemy import func

from sqlalchemy import select, func, column
from sqlalchemy.orm import aliased, subqueryload

from ...providers.sql_database import get_sessionmaker
from ...public_models import Document, DocumentList

from ..model import TrackedDocument

from .stats import get_document_statistics

logger = logging.getLogger(__name__)



def get_documents(doc_uuid_list: list[str | uuid.UUID]):
    """Return tracking records when matched to specified document UUID."""

    def _ensure_uuid(item):
        return uuid.UUID(hex=item) if isinstance(item, str) else item

    doc_uuid_list = [_ensure_uuid(item) for item in doc_uuid_list]

    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        stmt = select(TrackedDocument).where(
            TrackedDocument.id.in_(doc_uuid_list))
        result = session.execute(stmt)
        existing_objs = result.scalars().all()

    # The returned objects are detached from the closed session.
    return existing_objs


def list_documents(file_dir, start, length):
    """Return the list of files in cloud storage.
    """

    existing_objs = _list_tracking_records(start, length)
    table_stats = get_document_statistics()

    def _to_dict(_x: TrackedDocument):
        return Document(
            id = _x.id,
            status = _x.status,
            name = _x.filename,
            size_bytes = _x.size_bytes,
            modification_time = _x.file_modified_time,
            ingestion_time = _x.ingested_time,
            document_set_id = _x.document_set.id,
            document_set_name = _x.document_set.name
        )

    file_list = [_to_dict(x) for x in existing_objs]

    return DocumentList(
        documents = file_list,
        document_count = table_stats.document_count,
        table_updated_time = table_stats.table_updated_time
    )


def _list_tracking_records(start: Optional[int] = None, length: Optional[int] = None):
    """Return a page of tracking records.
    
    The implementation is an older known-performance technique. The technique
    creates a CTE (alternatively, a subquery could have been used) where each
    row is augmented with the windowing function ROW_NUMBER. Then the rows whose
    ROW_NUMBER values fall into the page range are choosen. Finally, the row
    data minus the ROW_NUMBER values are returned.
    """
    sessionmaker = get_sessionmaker()

    with sessionmaker() as session:

        paginate = start is not None and length is not None

        core_query = select(TrackedDocument)

        # Apply pagination if requested
        if paginate:
            # When paginating, we add a windowing function to the selected fields.
            cte_query = core_query.add_columns(
                func.row_number().over(order_by=TrackedDocument.filename).label('row_num')
            )
       
            # Create a CTE from the query.
            cte = cte_query.cte(name='row_numbered')

            # Alias the CTE
            WindowedTrackedDocument = aliased(element=TrackedDocument, alias=cte)

            # Query the CTE
            query = select(WindowedTrackedDocument).options(subqueryload(WindowedTrackedDocument.document_set)).where(
                # NOTE: Use the `column` function to directly reference the CTE column
                #   labeled 'row_num'. The reason is that 'row_num' is not a part of
                #   the model.
                # NOTE: ROW_NUMBER is 1-indexed. ROW_NUMBER is also inclusive.
                column('row_num').between(start + 1, start + length)
            )
        else:
            query = core_query.options(subqueryload(TrackedDocument.document_set))

        result = session.execute(query)
        existing_objs = result.scalars().all()

    return existing_objs


