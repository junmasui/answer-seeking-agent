"""
This module provides the node that generates an answer from the retrieved documents.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging

from ..providers.chat_llm import get_chat_llm
from .answer_citation_parser import AnswerCitationParser
from .internal_models import AgentPrompt
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


def answer_generator():
    prompt = get_chat_prompt(prompt_name=AgentPrompt.GENERATE_ANSWER)

    # LLM
    llm = get_chat_llm()

    # # Post-processing
    # def format_docs(docs):
    #     return '\n\n'.join(doc.page_content for doc in docs)

    # Chain
    rag_chain = prompt | llm | AnswerCitationParser()

    rag_chain = rag_chain.with_config({'run_name': 'answer_generator'})

    return rag_chain


def generate_answer(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    logger.info('---GENERATE---')
    question = state['question']
    documents = state['documents']
    history = state['messages']

    rag_chain = answer_generator()

    # RAG generation
    result = rag_chain.invoke(
        input={'documents': documents, 'chat_history': history, 'question': question},
        config={'configurable': {'documents': documents}},
    )

    # Update state with generated output
    stateUpdates = {'generation': result['generation'], 'answer': result['answer'], 'citations': result['citations']}
    return stateUpdates
