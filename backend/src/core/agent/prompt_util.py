import logging

from langchain_core.prompts import ChatPromptTemplate

from global_config import get_global_config

from ..prompt_mgr import list_prompts
from ..public_models import AgentPromptStatus
from .internal_models import AgentPrompt

logger = logging.getLogger(__name__)


def get_chat_prompt(prompt_name: AgentPrompt):
    """
    Retrieve a chat prompt from the database and return a ChatPromptTemplate.
    """
    if not isinstance(prompt_name, AgentPrompt):
        raise TypeError(f'prompt_name must be an instance of AgentPrompt enum, got {type(prompt_name)}')

    result = list_prompts(name=prompt_name.value, status=AgentPromptStatus.ACTIVE)
    if not result.prompts:
        raise ValueError(f"Prompt '{prompt_name.value}' not found in database.")

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
