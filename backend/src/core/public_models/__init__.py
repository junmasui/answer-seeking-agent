import enum

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
    ASC = 'asc'
    DESC = 'desc'
