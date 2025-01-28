"""
This module provides the node that rewrites the user questions 
so that the document retrieval returns with better relevancy.

See: Question Re-writer in https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/#llms
"""
import logging
import textwrap

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ..providers.chat_llm import get_chat_llm


logger = logging.getLogger(__name__)

### Question Re-writer

def get_question_rewriter():
    """
    """

    # LLM
    llm = get_chat_llm()

    # Prompt
    system = '''\
        You a question re-writer that converts an input question to a better version that is optimized
        for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning.'''
    human = '''\
        Here is the initial question:
        
        {question}
        
        Formulate an improved question.
        '''

    system = textwrap.dedent(system)
    human = textwrap.dedent(human)

    rewrite_prompt = ChatPromptTemplate.from_messages(
        [
            ('system', system),
            ('human', human ),
        ]
    )

    chain = rewrite_prompt | llm | StrOutputParser()

    chain = chain.with_config({'run_name': 'question_rewriter'})

    return chain

def rewrite_question(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state updates (dict): Updates with a re-phrased question
    """

    logger.info('---TRANSFORM QUERY---')
    question = state['question']

    question_rewriter = get_question_rewriter()

    # Re-write question
    better_question = question_rewriter.invoke({'question': question})

    # Update agent state with rewritten question.
    messages = [msg for msg in state['messages'] if msg.type == 'human']
    message = messages[-1]
    updatedMessage = message.model_copy(update={'content': better_question})

    stateUpdates = {
        'question': better_question,
        'messages': [ updatedMessage ]
    }

    return stateUpdates
