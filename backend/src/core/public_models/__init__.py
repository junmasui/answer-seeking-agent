import enum

from .agent import Answer, Citation, AnswerRequestBody

from .doc import BulkDeleteRequestBody, Document, DocumentList, DocumentStats, DocumentStatus, DocumentUpdateRequest

from .doc_set import (
    DocumentSet,
    DocumentSetList,
    DocumentSetStats,
    DocumentSetStatus,
    DocumentSetAddRequest,
    DocumentSetUpdateRequest,
)

from .ingest import IngestRequestBody

from .prompt import (
    AgentPrompt,
    AgentPromptList,
    AgentPromptStats,
    AgentPromptStatus,
    AgentPromptAddRequest,
    AgentPromptUpdateRequest,
)


class SortDirection(str, enum.Enum):
    ASC = 'asc'
    DESC = 'desc'
