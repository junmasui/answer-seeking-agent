"""
This module provides the node that generates an answer from the retrieved documents.

See https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#graph-state
"""

import logging
import textwrap

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ..providers.chat_llm import get_chat_llm
from .answer_citation_parser import AnswerCitationParser
from .prompt_util import get_prompt

logger = logging.getLogger(__name__)

PROMPT_NAME='Generate Answer'

def answer_generator():
    # Prompt
    human = '''\
        You are an assistant for question-answering tasks.
        Use the following chat history and pieces of retrieved source documents
        to answer the question. If you don't know the answer, just say
        that you don't know. Use three sentences maximum and keep
        the answer concise.

        Make your response as informative as possible and make sure every sentence is
        supported by the gathered information.
        Each sentence must be backed up by a citation from a retrieved source document,
        formatted as a footnote.
        The reference marks should be in the format [^1], [^2], [^3], etc.
        Each footnote should be formated as XML
        with a schema <footnote><docId></docId><sourceUrl></sourceUrl><fileName></fileName><pageNumber></pageNumber></footnote>.

        Question:
        
        {question}

        History:
        
        {chat_history}

        Source Documents:
        
        {documents}

        Answer:
        '''
    prompt = get_prompt(prompt_name=PROMPT_NAME, default_human_message=human)

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
    result = rag_chain.invoke(input={'documents': documents,
                                     'chat_history': history,
                                     'question': question},
                                     config={'configurable': {'documents': documents}})

    # Update state with generated output
    stateUpdates = {
        'generation': result['generation'],
        'answer': result['answer'],
        'citations': result['citations']
    }
    return stateUpdates