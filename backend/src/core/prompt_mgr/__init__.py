import textwrap

from core.agent.internal_models import AgentPrompt
from core.public_models import AgentPromptStatus

from . import initial_prompts
from .prompt import add_prompt, delete_prompt, get_prompt, get_prompt_statistics, list_prompts, update_prompt

# Explicitly define the exported names: these names are the contract of this module.
__all__ = [
    'add_prompt',
    'delete_prompt',
    'get_prompt',
    'get_prompt_statistics',
    'list_prompts',
    'update_prompt',
    'add_chat_prompt',
    'initial_prompts',
]


def add_chat_prompt(*, prompt_name: AgentPrompt, system_message: str = None, human_message: str = None):
    """Add a prompt in the database if it does not exist, using the provided defaults."""
    if not isinstance(prompt_name, AgentPrompt):
        raise TypeError(f'prompt_name must be an instance of AgentPrompt enum: {type(prompt_name)}')

    result = list_prompts(name=prompt_name.value, status=AgentPromptStatus.ACTIVE)

    if result.prompts:
        return

    if system_message:
        system_message = textwrap.dedent(system_message)
    if human_message:
        human_message = textwrap.dedent(human_message)
    add_prompt(
        name=prompt_name.value,
        status=AgentPromptStatus.ACTIVE,
        human_message=human_message,
        system_message=system_message,
    )
