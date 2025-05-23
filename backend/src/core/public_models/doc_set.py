import enum
from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import Field

from .base import CamelModel

#
# Domain Models
#


class DocumentSetStatus(str, enum.Enum):
    ACTIVE = 'active'
    CLOSED = 'closed'
    FROZEN = 'frozen'
    DEACTIVATED = 'deactivated'


class DocumentSet(CamelModel):
    id: UUID
    name: str = Field(description='Name of document set.')
    status: DocumentSetStatus = Field(description='Status.')
    is_new_doc_default: bool = Field(description='True if default document set for new documents')
    is_public_viewable: bool = Field(description='True if documents are publicly visible')


class DocumentSetStats(CamelModel):
    document_set_count: int = None
    table_updated_time: Optional[datetime] = None


#
#
#


class DocumentSetList(CamelModel):
    document_sets: list[DocumentSet]
    document_set_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#


class DocumentSetAddRequest(CamelModel):
    name: str = Field(description='Name of document set.')
    is_new_doc_default: bool = Field(description='True if default document set for new documents')
    is_public_viewable: bool = Field(description='True if documents are publicly visible')


class DocumentSetUpdateRequest(CamelModel):
    name: Optional[str] = Field(description='Name of document set.', default=None)
    is_new_doc_default: Optional[bool] = Field(
        description='True if default document set for new documents', default=None
    )
    is_public_viewable: Optional[bool] = Field(description='True if documents are publicly visible', default=None)
