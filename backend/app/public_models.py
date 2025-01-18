from typing import Union, Optional
import logging
from uuid import UUID
from datetime import datetime
import enum

from pydantic import BaseModel, ConfigDict
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
    name: str
    status: DocumentStatus
    size_bytes: int
    modification_time: datetime
    ingestion_time: Optional[datetime] = None


class DocumentList(CamelModel):
    documents: list[Document]
    document_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None

class DocumentStats(CamelModel):
    document_count: int = None
    table_updated_time: Optional[datetime] = None


class IngestRequestBody(CamelModel):
    doc_uuid: Optional[list[UUID]] = None


class Answer(CamelModel):
    question: str
    answer: str
    thread_id: UUID
    user_id: Optional[str] = None
