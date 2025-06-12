"""
This module provides the node that generates an answer from the retrieved documents.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging

from core.agent.agent_state import GraphState

from ..providers.chat_llm import get_chat_llm
from .answer_citation_parser import AnswerCitationParser
from .internal_models import AgentPromptName
from .prompt_util import get_chat_prompt

logger = logging.getLogger(__name__)


def answer_generator():
    """
    Create an answer generation chain for RAG (Retrieval-Augmented Generation).

    Combines a chat prompt, language model, and answer citation parser to generate answers from
    retrieved documents with proper citation extraction.
    """
    prompt = get_chat_prompt(prompt_name=AgentPromptName.GENERATE_ANSWER)

    # LLM
    llm = get_chat_llm()

    # # Post-processing
    # def format_docs(docs):
    #     return '\n\n'.join(doc.page_content for doc in docs)

    # Chain
    rag_chain = prompt | llm | AnswerCitationParser()

    rag_chain = rag_chain.with_config({'run_name': 'answer_generator'})

    return rag_chain


def generate_answer(state: GraphState):
    """
    Generate an answer using the RAG agent.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updates to the graph state with the generated answer and citations

    """
    logger.info('---GENERATE ANSWER---')
    question = state.question
    documents = state.documents
    history = state.messages

    chain = answer_generator()

    # RAG generation
    result = chain.invoke(
        input={'documents': documents, 'chat_history': history, 'question': question},
        config={'configurable': {'documents': documents}},
    )

    # Update state with generated output
    state_updates = {'generation': result['generation'], 'answer': result['answer'], 'citations': result['citations']}
    return state_updates
