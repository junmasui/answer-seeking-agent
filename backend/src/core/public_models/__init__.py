import enum

from .agent import Answer, AnswerRequestBody, Citation
from .doc import BulkDeleteRequestBody, Document, DocumentList, DocumentStats, DocumentStatus, DocumentUpdateRequest
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


class SortDirection(str, enum.Enum):
    ASC = 'asc'
    DESC = 'desc'
