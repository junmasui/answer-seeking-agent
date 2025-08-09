import enum
from datetime import datetime
from typing import Optional
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

    id: UUID
    name: str = Field(description='File name of document.')
    status: DocumentStatus = Field(description='Status.')
    size_bytes: int = Field(description='Raw file size in bytes.')
    modification_time: datetime = Field(description='Latest time when document was modified.')
    ingestion_time: Optional[datetime] = Field(default=None, description='Time when document was ingested.')
    source_url: Optional[str] = Field(default=None, description='Source URL of this document')
    content_type: Optional[str] = Field(default=None, description='MIME content type of this document')
    download_time_utc: Optional[datetime] = Field(default=None, description='Time when document was downloaded.')
    document_set_id: Optional[UUID] = Field(description='Document set UUID.')
    document_set_name: Optional[str] = Field(description='Document set name.')


class DocumentStats(CamelModel):
    """Provides statistics about documents, such as the total count and last update time."""

    document_count: int = None
    table_updated_time: Optional[datetime] = None


#
#
#


class DocumentList(CamelModel):
    """Represents a list of documents, along with optional count and update time information."""

    documents: list[Document]
    document_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#
class DocumentUpdateRequest(CamelModel):
    """Represents a request to update a document."""

    document_set_id: Optional[UUID] = Field(description='Document set UUID.')


class BulkDeleteRequestBody(CamelModel):
    """Represents a request to delete multiple documents."""

    doc_uuids: list[UUID]


class DocumentUploadFormData(CamelModel):
    """
    Represents the form data for uploading a document.

    The form data includes details about the document set, chunks, and source.
    """

    document_set_id: UUID
    total_chunks: int
    chunk_index: int
    source_url: str
    content_type: str
    download_time_utc_str: str
