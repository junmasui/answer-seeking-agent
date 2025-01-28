"""
This module provides the node that evaluates whether the retrieved documents are relevent
to addressing the user question.

See: Retrieval Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
import logging
from functools import cache
import textwrap

from .grader_util import build_grader

from .internal_models import GradeDocuments


logger = logging.getLogger(__name__)

@cache
def get_retrieval_grader():
    """
    """

    # Instructions
    system = '''\
        You are a grader assessing relevance of a retrieved document to a user question.
        It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.'''
    human = '''\
        Retrieved document:
        
        {document}
        
        User question:
        
        {question}'''
    system = textwrap.dedent(system)
    human = textwrap.dedent(human)

    retrieval_grader = build_grader(system, human, GradeDocuments, 'retrieval_grader')

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
    for d in documents:
        score = retrieval_grader.invoke(
            {'question': question, 'document': d.page_content}
        )
        grade = score.binary_score if score is not None else 'no'
        if grade == 'yes':
            logger.info('---GRADE: DOCUMENT RELEVANT---')
            filtered_docs.append(d)
        else:
            logger.info('---GRADE: DOCUMENT NOT RELEVANT---')
            continue
    
    # Keep only the relevant documents
    return { 'documents': filtered_docs }