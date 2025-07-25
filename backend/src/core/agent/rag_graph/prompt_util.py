import logging

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)

from ...lib_config import get_lib_config
from ...prompt_mgr import list_prompts
from ...public_models import AgentPromptStatus
from ..internal_models import AgentPromptName

logger = logging.getLogger(__name__)


def get_chat_prompt(prompt_name: str):
    """Retrieve a chat prompt from the database and return a ChatPromptTemplate."""
    if prompt_name not in AgentPromptName:
        raise TypeError(f'prompt_name must be a valid AgentPromptName, got {prompt_name}')

    result = list_prompts(name=prompt_name, status=AgentPromptStatus.ACTIVE)
    if not result.prompts:
        raise ValueError(f"Prompt '{prompt_name}' not found in database.")

    prompt = result.prompts[0]
    system_message = prompt.system_message
    human_message = prompt.human_message
    include_history = prompt.include_history

    messages = []
    if system_message:
        # HuggingFace does not have native support for structured output
        # See https://python.langchain.com/docs/how_to/structured_output/#custom-parsing
        #
        # Thus we support two modes:
        # - structured output
        # - custom instructions and parsing
        has_structured_output = get_lib_config().llm_has_structured_output

        if not has_structured_output:
            system_message = system_message + '\n\n{format_instructions}'

        system_message = SystemMessagePromptTemplate.from_template(system_message)
        messages.append(system_message)

    if include_history:
        history_placeholder = MessagesPlaceholder('chat_history')
        messages.append(history_placeholder)

    if human_message:
        human_message = HumanMessagePromptTemplate.from_template(human_message)
        messages.append(human_message)

    chat_prompt = ChatPromptTemplate.from_messages(messages)
    return chat_prompt
