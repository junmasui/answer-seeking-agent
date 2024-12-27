"""
This module provides the node that evaluates whether an generated answer contains hallucinations.

See: Hallucination Grader in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
from functools import cache
import textwrap

from .internal_models import GradeHallucinations
from .grader_util import build_grader


@cache
def get_hallucination_grader():
    """
    """

    # Instructions
    system = '''\
        You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.
        Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.'''
    human = '''\
        Set of facts:

        {documents}
        
        LLM generation:
        
        {generation}
        '''
    system = textwrap.dedent(system)
    human = textwrap.dedent(human)

    hallucination_grader = build_grader(system, human, GradeHallucinations, 'hallucination_grader')

    return hallucination_grader

