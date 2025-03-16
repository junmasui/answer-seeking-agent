from uuid import UUID


from .base import CamelModel

#
# Operator Models
#
class IngestRequestBody(CamelModel):
    doc_uuids: list[UUID]
