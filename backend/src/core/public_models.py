from typing import Union, Optional
import logging
from uuid import UUID
from datetime import datetime
import enum

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """
    See https://medium.com/@drewscatterday/convert-fastapi-snake-case-json-response-to-camel-case-d94c20e92b52
    and https://stackoverflow.com/questions/67995510/how-to-inflect-from-snake-case-to-camel-case-post-the-pydantic-schema-validation/77424889#77424889
    """
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    QUEUING = "queuing"
    QUEUED = "queued"
    INGESTING = "ingesting"
    INGESTED = "ingested"
    ERROR = "errors"

class Document(CamelModel):
    id: UUID
    name: str = Field(
        description="File name of document.",
    )
    status: DocumentStatus = Field(
        description="Status.",
    )
    size_bytes: int = Field(
        description="Raw file size in bytes.",
    )
    modification_time: datetime = Field(
        description="Latest time when document was modified.",
    )
    ingestion_time: Optional[datetime] = Field(
        default=None,
        description="Time when document was ingested.",
    )
    document_set_id: Optional[UUID] = Field(
        description="Document set UUID.",
    )
    document_set_name: Optional[str] = Field(
        description="Document set name.",
    )

class DocumentUpdateRequest(CamelModel):
    document_set_id: Optional[UUID] = Field(
        description="Document set UUID.",
    )


class DocumentList(CamelModel):
    documents: list[Document]
    document_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


class DocumentSet(CamelModel):
    id: UUID
    name: str = Field(
        description="Name of document set.",
    )

class DocumentSetList(CamelModel):
    document_sets: list[DocumentSet]
    document_set_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


class DocumentStats(CamelModel):
    document_count: int = None
    table_updated_time: Optional[datetime] = None


class IngestRequestBody(CamelModel):
    doc_uuids: list[UUID]

class Citation(CamelModel):
    doc_uuid: UUID = Field(
        description="Document UUID.",
    )
    text: str = Field(
        description="Citation text.",
    )
    file_name: Optional[str] = Field(
        default=None,
        description="File name of source document.",
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Page number of text within source document.",
    )


class Answer(CamelModel):
    question: str = Field(
        description="User's question.",
    )
    answer: str = Field(
        description="Answer to the user's question with citations.",
    )
    citations: list[Citation] = Field(
        description="List of citations.",
    )
    thread_id: UUID = Field(
        description="Conversation UUID. A conversation is a sequence of questions and answers.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User UUID associated this question and answer.",
    )
