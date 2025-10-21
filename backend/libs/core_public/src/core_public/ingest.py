from typing import Annotated, Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel


#
# Operator Models
#
class IngestRequestBody(CamelModel):
    """
    Specifies documents to be ingested.

    Use this to request ingestion for specific documents, document sets, or all uploaded documents.
    """

    doc_uuids: Annotated[Optional[list[UUID]], Field(description='A list of document UUIDs to ingest.', default=None)]
    doc_set_uuid: Annotated[
        Optional[UUID | list[UUID]],
        Field(description='A document set UUID or a list of document set UUIDs to ingest.', default=None),
    ]
    all_uploaded: Annotated[
        Optional[bool], Field(description='A flag to ingest all uploaded documents.', default=None)
    ]
