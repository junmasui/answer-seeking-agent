import enum
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel

#
# Domain Models
#


class DocumentStatus(str, enum.Enum):
    """Enumeration for the status of a document."""

    UPLOADING = 'uploading'
    UPLOADED = 'uploaded'
    QUEUING = 'queuing'
    QUEUED = 'queued'
    INGESTING = 'ingesting'
    INGESTED = 'ingested'
    ERROR = 'errors'


class Document(CamelModel):
    """Represents a document with its metadata, status, and content information."""

    id: Annotated[UUID, Field(description='ID of the document.')]
    name: Annotated[str, Field(description='File name of document.')]
    status: Annotated[DocumentStatus, Field(description='Status.')]
    size_bytes: Annotated[int, Field(description='Raw file size in bytes.')]
    modification_time: Annotated[datetime, Field(description='Latest time when document was modified.')]
    ingestion_time: Annotated[
        Optional[datetime], Field(default=None, description='Time when document was ingested.')
    ]
    source_url: Annotated[Optional[str], Field(default=None, description='Source URL of this document')]
    content_type: Annotated[Optional[str], Field(default=None, description='MIME content type of this document')]
    download_time_utc: Annotated[
        Optional[datetime], Field(default=None, description='Time when document was downloaded.')
    ]
    document_set_id: Annotated[Optional[UUID], Field(description='Document set UUID.')]
    document_set_name: Annotated[Optional[str], Field(description='Document set name.')]


class DocumentStats(CamelModel):
    """Provides statistics about documents, such as the total count and last update time."""

    document_count: Annotated[Optional[int], Field(description='Total number of documents.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the document table was updated.', default=None)
    ]


#
#
#


class DocumentList(CamelModel):
    """Represents a list of documents, along with optional count and update time information."""

    documents: Annotated[list[Document], Field(description='List of documents.')]
    document_count: Annotated[Optional[int], Field(description='Total number of documents.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the document table was updated.', default=None)
    ]


#
# Operator Models
#
class DocumentUpdateRequest(CamelModel):
    """Represents a request to update a document."""

    document_set_id: Annotated[Optional[UUID], Field(description='Document set UUID.')]


class BulkDeleteRequestBody(CamelModel):
    """Represents a request to delete multiple documents."""

    doc_uuids: Annotated[list[UUID], Field(description='A list of document UUIDs to delete.')]


class DocumentUploadFormData(CamelModel):
    """
    Represents the form data for uploading a document.

    The form data includes details about the document set, chunks, and source.
    """

    document_set_id: Annotated[UUID, Field(description='The UUID of the document set.')]
    total_chunks: Annotated[int, Field(description='The total number of chunks for the document.')]
    chunk_index: Annotated[int, Field(description='The index of the current chunk.')]
    source_url: Annotated[str, Field(description='The source URL of the document.')]
    content_type: Annotated[str, Field(description='The MIME content type of the document.')]
    download_time_utc_str: Annotated[str, Field(description='The download time of the document in UTC format.')]
