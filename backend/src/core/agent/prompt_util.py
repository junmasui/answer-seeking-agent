from functools import cache
import textwrap
import logging

from langchain_core.prompts import ChatPromptTemplate

from global_config import get_global_config

from ..public_models import AgentPromptStatus
from ..prompt_mgr import list_prompts, add_prompt

logger = logging.getLogger(__name__)

def get_chat_prompt(prompt_name: str):
    """
    Retrieve a chat prompt from the database and return a ChatPromptTemplate.
    """
    result = list_prompts(name=prompt_name, status=AgentPromptStatus.ACTIVE)
    if not result.prompts:
        raise ValueError(f"Prompt '{prompt_name}' not found in database.")

    prompt = result.prompts[0]
    system_message = prompt.system_message
    human_message = prompt.human_message

    messages = []
    if system_message:

        # HuggingFace does not have native support for structured output
        # See https://python.langchain.com/docs/how_to/structured_output/#custom-parsing
        #
        # Thus we support two modes:
        # - structured output
        # - custom instructions and parsing
        has_structured_output = get_global_config().llm_has_structured_output

        if not has_structured_output:
            system_message = system_message + '\n\n{format_instructions}'  

        messages.append(('system', system_message))

    if human_message:
        messages.append(('human', human_message))


    chat_prompt = ChatPromptTemplate.from_messages(messages)
    return chat_prompt

def add_chat_prompt(*, prompt_name: str, default_system_message: str = None, default_human_message: str = None):
    """
    Add a prompt in the database if it does not exist, using the provided defaults.
    """
    result = list_prompts(name=prompt_name, status=AgentPromptStatus.ACTIVE)

    if result.prompts:
        return

    if default_system_message:
        default_system_message = textwrap.dedent(default_system_message)
    if default_human_message:
        default_human_message = textwrap.dedent(default_human_message)
    add_prompt(prompt_name, status=AgentPromptStatus.ACTIVE, human_message=default_human_message, system_message=default_system_message)