import logging
import uuid
from typing import Optional

from core_db.db_models import DbTrackedDocument
from core_db.doc_mgr.doc.query import list_tracking_records
from core_public import Document, DocumentList

from core_public import DocumentStatus

from .stats import get_document_statistics

logger = logging.getLogger(__name__)

def list_documents(
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
    Return a list of documents, with optional filtering, sorting, and pagination.

    This function retrieves a list of documents from the database, applies various
    filters based on the provided parameters, and can paginate the results. It also
    gathers statistics about the documents table.

    Args:
        doc_set_id: Optional. A single UUID or a list of UUIDs to filter documents
            by their document set.
        status: Optional. A single DocumentStatus or a list of statuses to filter
            documents by.
        file_name: Optional. A string to filter documents by the start of their
            filename (case-insensitive).
        start: Optional. The starting index for pagination.
        length: Optional. The number of documents to return for pagination.
        sort_by: Optional. A list of tuples, where each tuple contains a field name
            and a SortDirection, to specify the sorting of the results.
        document_set_name: Optional. A string to filter documents by the start of
            their document set name (case-insensitive).
        content_type: Optional. A string to filter documents by the start of their
            content type (case-insensitive).
        source_url: Optional. A string to filter documents by the start of their
            source URL (case-insensitive).

    Returns:
        A DocumentList object containing the list of documents and table statistics.

    """
    existing_objs = list_tracking_records(
        doc_set_id=doc_set_id,
        status=status,
        file_name=file_name,
        start=start,
        length=length,
        sort_by=sort_by,
        document_set_name=document_set_name,
        content_type=content_type,
        source_url=source_url,
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


