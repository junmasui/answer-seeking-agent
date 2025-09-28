from typing import Optional
from uuid import UUID

from .base import CamelModel


#
# Operator Models
#
class IngestRequestBody(CamelModel):
    """
    Specifies documents to be ingested.

    Use this to request ingestion for specific documents, document sets, or all uploaded documents.
    """

    doc_uuids: Optional[list[UUID]] = None
    doc_set_uuid: Optional[UUID | list[UUID]] = None
    all_uploaded: Optional[bool] = None
