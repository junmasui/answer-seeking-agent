from enum import StrEnum


class NodeName(StrEnum):
    """
    Defines standardized names for nodes within the agent graph.

    This ensures consistency and avoids typos when referring to nodes in graph definitions and
    logic.
    """

    QUERY_DOCUMENTS = 'query_documents'
    GRADE_RELEVANCIES = 'grade_relevancies'
    REWRITE_QUERY = 'rewrite_query'
    GRADE_HALLUCINATION = 'grade_hallucination'
    GRADE_ANSWER = 'grade_answer'
    ACCEPT_ANSWER = 'accept_answer'
    REDO_DOCUMENT_RETRIEVAL = 'redo_document_retrieval'
    REDO_ANSWER_GENERATION = 'redo_answer_generation'
    ADD_QUERY_TO_HISTORY = 'add_query_to_history'
    ADD_RESPONSE_TO_HISTORY = 'add_response_to_history'
    RETRIEVE_DOCUMENTS = 'retrieve_documents'
    GENERATE_ANSWER = 'generate_answer'

    BAD_INPUT = 'bad_input'
    BAD_RETRIEVAL = 'bad_retrieval'
    BAD_RESPONSE = 'bad_response'

    RETRIEVAL_EXIT = 'retrieval_exit'
    RESPONSE_EXIT = 'response_exit'

    INPUT_GUARD = 'input_guard'
    RETRIEVAL_GUARD = 'retrieval_guard'
    RESPONSE_GUARD = 'response_guard'

    INPUT_GUARD_START = 'input_guard_start'
    DETECT_PROMPT_INJECTION = 'detect_prompt_injection'
    DETECT_PRIVACY_VIOLATION = 'detect_privacy_violation'
    DETECT_TOXIC_INPUT = 'detect_toxic_input'
    INPUT_GUARD_DECISION = 'input_guard_decision'

    RETRIEVAL_GUARD_START = 'document_guard_start'
    DETECT_TOXIC_CONTENT = 'detect_toxic_content'
    GATHER_RELEVANT_DOCUMENTS = 'gather_documents'
    RETRIEVAL_GUARD_DECISION = 'document_guard_decision'

    RESPONSE_GUARD_START = 'response_guard_start'
    DETECT_SENSITIVE_INFO = 'detect_sensitive_info'
    DETECT_TOXIC_RESPONSE = 'detect_toxic_response'
    RESPONSE_GUARD_DECISION = 'response_guard_decision'


class UserInputGrade(StrEnum):
    """
    Represents the possible overall grades for user input.

    These grades are used to determine the next step in the agent graph after input validation.
    """

    REJECT_USER_INPUT = 'reject user input'
    ACCEPT_USER_INPUT = 'accept user input'


class RetrievalOverallGrade(StrEnum):
    """
    Represents the possible overall grades for document retrieval.

    These grades guide the agent on whether to proceed with answer generation, retry retrieval, or
    reject the retrieval attempt.
    """

    RELEVANT_DOCS_FOUND = 'relevant docs found'
    NO_RELEVANT_DOCS = 'no relevant docs'
    REJECT_RETRIEVAL = 'reject retrieval'


class ResponseOverallGrade(StrEnum):
    """
    Represents the possible overall grades for the generated response.

    These grades determine whether the answer is accepted, rejected, or if parts of the process need
    to be redone.
    """

    REDO_DOCUMENT_RETRIEVAL = 'redo document retrieval'
    REDO_ANSWER_GENERATION = 'redo answer generation'
    ACCEPT_ANSWER = 'accept answer'
    REJECT_ANSWER = 'reject answer'
