import enum
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import CamelModel

#
# Domain Models
#


class DocumentSetStatus(str, enum.Enum):
    """Enumeration for the status of a document set."""

    ACTIVE = 'active'
    CLOSED = 'closed'
    FROZEN = 'frozen'
    DEACTIVATED = 'deactivated'


class DocumentSet(CamelModel):
    """
    Represent metadata regarding a set of documents.

    The metadata includes its status and properties like default status for new documents and public
    visibility.
    """

    id: UUID
    name: str = Field(description='Name of document set.')
    status: DocumentSetStatus = Field(description='Status.')
    is_new_doc_default: bool = Field(description='True if default document set for new documents')
    is_public_viewable: bool = Field(description='True if documents are publicly visible')


class DocumentSetStats(CamelModel):
    """
    Provides statistics about document sets.

    The statistics include the total count and last update time.
    """

    document_set_count: int = None
    table_updated_time: Optional[datetime] = None


#
#
#


class DocumentSetList(CamelModel):
    """
    Represents list of document sets.

    Additional information is the optional total count and update time information.
    """

    document_sets: list[DocumentSet]
    document_set_count: Optional[int] = None
    table_updated_time: Optional[datetime] = None


#
# Operator Models
#


class DocumentSetAddRequest(CamelModel):
    """Represents a request to add a new document set."""

    name: str = Field(description='Name of document set.')
    is_new_doc_default: bool = Field(description='True if default document set for new documents')
    is_public_viewable: bool = Field(description='True if documents are publicly visible')


class DocumentSetUpdateRequest(CamelModel):
    """Represents a request to update an existing document set."""

    name: Optional[str] = Field(description='Name of document set.', default=None)
    is_new_doc_default: Optional[bool] = Field(
        description='True if default document set for new documents', default=None
    )
    is_public_viewable: Optional[bool] = Field(description='True if documents are publicly visible', default=None)
