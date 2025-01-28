"""
This module provides the node that evaluates whether an generated answer addresses the question.

See: Answer Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
from functools import cache
import textwrap

from .internal_models import GradeAnswer
from .grader_util import build_grader

@cache
def get_answer_grader():
    """
    """

    # Instructions
    system = '''\
        You are a grader assessing whether an answer addresses / resolves a question
        Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question.'''
    human = '''\
        User question:

        {question}

        LLM generation:
        
        {generation}'''
    
    system = textwrap.dedent(system)
    human = textwrap.dedent(human)

    answer_grader = build_grader(system, human, GradeAnswer, 'answer_grader')

    return answer_grader

