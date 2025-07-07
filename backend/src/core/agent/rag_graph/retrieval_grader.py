"""
This module provides the node that evaluates whether the retrieved documents are relevent to
addressing the user question.

See: Retrieval Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""

import logging
from functools import cache

from ..internal_models import AgentPromptName
from .agent_state import GraphState
from .grader_util import build_grader
from .internal_models import GradeDocuments
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


@cache
def get_retrieval_grader():
    """
    Initializes and returns a retrieval grading chain.

    This function builds a grader that uses a chat prompt (GRADE_RETRIEVED_DOCUMENTS) and a Pydantic
    model (GradeDocuments) for structured output. The grader is cached to avoid reinitialization.
    """
    prompt = get_chat_prompt(prompt_name=AgentPromptName.GRADE_RETRIEVED_DOCUMENTS)

    retrieval_grader = build_grader(prompt, GradeDocuments, 'retrieval_grader')

    return retrieval_grader


def grade_document_relevancies(state: GraphState):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with relevant documents

    """
    logger.info('---CHECK DOCUMENT RELEVANCE TO QUESTION---')

    question = state.question
    documents = state.documents

    retrieval_grader = get_retrieval_grader()

    # Score each doc
    document_relevancy = []
    for doc in documents:
        score = retrieval_grader.invoke({'question': question, 'document': doc.page_content})
        grade = score.binary_score if score is not None else 'no'

        if grade == 'yes':
            logger.info('---GRADE: DOCUMENT RELEVANT---')
        else:
            logger.info('---GRADE: DOCUMENT NOT RELEVANT---')

        document_relevancy.append(10 if grade == 'yes' else 0)

    # Keep only the relevant documents
    return {'document_relevancy': document_relevancy}
