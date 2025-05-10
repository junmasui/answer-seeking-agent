import logging

from .util import add_chat_prompt
from ..agent.internal_models import AgentPrompt
from ..signals import db_predefined_data_handler

logger = logging.getLogger(__name__)

# Register the original prompts at startup

@db_predefined_data_handler
def register_initial_prompts(sender):
    if sender.is_worker:
        return

    logger.info('adding predefined prompts')
    add_chat_prompt(
        prompt_name=AgentPrompt.GENERATE_ANSWER,
        human_message='''\
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
    )
    add_chat_prompt(
        prompt_name=AgentPrompt.REWRITE_QUERY,
        system_message='''\
            You a question re-writer that converts an input question to a better version that is optimized
            for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning.''',
        human_message='''\
            Here is the initial question:
            
            {question}
            
            Formulate an improved question.
        '''
    )
    add_chat_prompt(
        prompt_name=AgentPrompt.GRADE_RETRIEVED_DOCUMENTS,
        system_message='''\
            You are a grader assessing relevance of a retrieved document to a user question.
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.''',
        human_message='''\
            Retrieved document:
            
            {document}
            
            User question:
            
            {question}'''
    )
    add_chat_prompt(
        prompt_name=AgentPrompt.GRADE_ANSWER,
        system_message='''\
            You are a grader assessing whether an answer addresses / resolves a question
            Give a binary score 'yes' or 'no'. Yes' means that the answer resolves the question.''',
        human_message='''\
            User question:

            {question}

            LLM generation:
            
            {generation}'''
    )
    add_chat_prompt(
        prompt_name=AgentPrompt.GRADE_HALLUCINATION,
        system_message='''\
            You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.

            Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.''',
        human_message='''\
            Set of facts:

            {documents}
            
            LLM generation:
            
            {generation}
            '''
    )
