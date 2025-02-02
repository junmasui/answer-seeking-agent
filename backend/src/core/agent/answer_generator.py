"""
This module provides the node that generates an answer from the retrieved documents.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging
import textwrap

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ..providers.chat_llm import get_chat_llm


logger = logging.getLogger(__name__)


def answer_generator():
    # Prompt
    human = '''\
        You are an assistant for question-answering tasks.
        Use the following chat history and pieces of retrieved context
        to answer the question. If you don't know the answer, just say
        that you don't know. Use three sentences maximum and keep
        the answer concise.

        Question:
        
        {question}

        History:
        
        {chat_history}

        Context:
        
        {context}

        Answer:
        '''
    # We maintain multiline strings that are indented in the codebase but not indented when calling the LLM API.
    human = textwrap.dedent(human)
    prompt =  ChatPromptTemplate.from_messages(
        [
            ('human', human),
        ]
    )
    ### prompt = hub.pull('rlm/rag-prompt')

    # LLM
    llm = get_chat_llm()


    # # Post-processing
    # def format_docs(docs):
    #     return '\n\n'.join(doc.page_content for doc in docs)


    # Chain
    rag_chain = prompt | llm | StrOutputParser()

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
    generation = rag_chain.invoke({'context': documents, 'chat_history': history, 'question': question})

    # Update state with generated output
    stateUpdates = { 'generation': generation }
    return stateUpdates