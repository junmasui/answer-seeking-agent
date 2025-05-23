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
    UPLOADING = 'uploading'
    UPLOADED = 'uploaded'
    QUEUING = 'queuing'
    QUEUED = 'queued'
    INGESTING = 'ingesting'
    INGESTED = 'ingested'
    ERROR = 'errors'


class Document(CamelModel):
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
    document_count: int = None
    table_updated_time: Optional[datetime] = None


#
#
#


class DocumentList(CamelModel):
    documents: list[Document]
    document_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#
class DocumentUpdateRequest(CamelModel):
    document_set_id: Optional[UUID] = Field(description='Document set UUID.')


class BulkDeleteRequestBody(CamelModel):
    doc_uuids: list[UUID]
