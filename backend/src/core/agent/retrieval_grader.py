"""
This module provides the node that evaluates whether the retrieved documents are relevent
to addressing the user question.

See: Retrieval Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
import logging
from functools import cache
import textwrap

from .grader_util import build_grader
from .prompt_util import get_chat_prompt

from .internal_models import GradeDocuments, AgentPrompt


logger = logging.getLogger(__name__)

@cache
def get_retrieval_grader():
    """
    """

    prompt = get_chat_prompt(prompt_name=AgentPrompt.GRADE_RETRIEVED_DOCUMENTS)

    retrieval_grader = build_grader(prompt, GradeDocuments, 'retrieval_grader')

    return retrieval_grader

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with relevant documents
    """

    logger.info('---CHECK DOCUMENT RELEVANCE TO QUESTION---')

    question = state['question']
    documents = state['documents']

    retrieval_grader = get_retrieval_grader()

    # Score each doc
    filtered_docs = []
    for doc in documents:
        score = retrieval_grader.invoke(
            {'question': question, 'document': doc.page_content}
        )
        grade = score.binary_score if score is not None else 'no'
        if grade == 'yes':
            logger.info('---GRADE: DOCUMENT RELEVANT---')
            filtered_docs.append(doc)
        else:
            logger.info('---GRADE: DOCUMENT NOT RELEVANT---')
            continue
    
    # Keep only the relevant documents
    return { 'documents': filtered_docs }