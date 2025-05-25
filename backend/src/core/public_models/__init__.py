import enum

from .agent import Answer, AnswerRequestBody, Citation
from .doc import (
    BulkDeleteRequestBody,
    Document,
    DocumentList,
    DocumentStats,
    DocumentStatus,
    DocumentUpdateRequest,
    DocumentUploadFormData,
)
from .doc_set import (
    DocumentSet,
    DocumentSetAddRequest,
    DocumentSetList,
    DocumentSetStats,
    DocumentSetStatus,
    DocumentSetUpdateRequest,
)
from .ingest import IngestRequestBody
from .prompt import (
    AgentPrompt,
    AgentPromptAddRequest,
    AgentPromptList,
    AgentPromptStats,
    AgentPromptStatus,
    AgentPromptUpdateRequest,
)

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'Answer',
    'AnswerRequestBody',
    'Citation',
    'BulkDeleteRequestBody',
    'Document',
    'DocumentList',
    'DocumentStats',
    'DocumentStatus',
    'DocumentUpdateRequest',
    'DocumentUploadFormData',
    'DocumentSet',
    'DocumentSetAddRequest',
    'DocumentSetList',
    'DocumentSetStats',
    'DocumentSetStatus',
    'DocumentSetUpdateRequest',
    'IngestRequestBody',
    'AgentPrompt',
    'AgentPromptAddRequest',
    'AgentPromptList',
    'AgentPromptStats',
    'AgentPromptStatus',
    'AgentPromptUpdateRequest',
    'SortDirection',
]


class SortDirection(str, enum.Enum):
    """Specifies the direction for sorting, either ascending or descending."""
    ASC = 'asc'
    DESC = 'desc'
