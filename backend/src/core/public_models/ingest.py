from uuid import UUID
from typing import Optional

from .base import CamelModel

#
# Operator Models
#
class IngestRequestBody(CamelModel):
    doc_uuids: Optional[list[UUID]] = None
    doc_set_uuid: Optional[UUID | list[UUID]] = None
    all_uploaded: Optional[bool] = None
