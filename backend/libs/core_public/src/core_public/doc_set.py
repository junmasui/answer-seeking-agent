import enum
from datetime import datetime
from typing import Annotated, Optional
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

    id: Annotated[UUID, Field(description='ID of the document set.')]
    name: Annotated[str, Field(description='Name of document set.')]
    status: Annotated[DocumentSetStatus, Field(description='Status.')]
    is_new_doc_default: Annotated[bool, Field(description='True if default document set for new documents')]
    is_public_viewable: Annotated[bool, Field(description='True if documents are publicly visible')]


class DocumentSetStats(CamelModel):
    """
    Provides statistics about document sets.

    The statistics include the total count and last update time.
    """

    document_set_count: Annotated[Optional[int], Field(description='Total number of document sets.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the document set table was updated.', default=None)
    ]


#
#
#


class DocumentSetList(CamelModel):
    """
    Represents list of document sets.

    Additional information is the optional total count and update time information.
    """

    document_sets: Annotated[list[DocumentSet], Field(description='List of document sets.')]
    document_set_count: Annotated[Optional[int], Field(description='Total number of document sets.', default=None)]
    table_updated_time: Annotated[
        Optional[datetime], Field(description='Last time the document set table was updated.', default=None)
    ]


#
# Operator Models
#


class DocumentSetAddRequest(CamelModel):
    """Represents a request to add a new document set."""

    name: Annotated[str, Field(description='Name of document set.')]
    is_new_doc_default: Annotated[bool, Field(description='True if default document set for new documents')]
    is_public_viewable: Annotated[bool, Field(description='True if documents are publicly visible')]


class DocumentSetUpdateRequest(CamelModel):
    """Represents a request to update an existing document set."""

    name: Annotated[Optional[str], Field(description='Name of document set.', default=None)]
    is_new_doc_default: Annotated[
        Optional[bool], Field(description='True if default document set for new documents', default=None)
    ]
    is_public_viewable: Annotated[
        Optional[bool], Field(description='True if documents are publicly visible', default=None)
    ]
