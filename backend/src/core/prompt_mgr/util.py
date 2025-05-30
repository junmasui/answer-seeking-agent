import textwrap
from typing import Optional

from ..agent.internal_models import AgentPromptName
from ..public_models import AgentPromptStatus, OwnerType
from .prompt.add import add_prompt
from .prompt.query import list_prompts


def add_chat_prompt(
    *,
    prompt_name: str,
    owner_type: OwnerType,
    system_message: Optional[str] = None,
    human_message: Optional[str] = None,
    include_history: Optional[bool] = None,
):
    """Add a prompt in the database if it does not exist, using the provided defaults."""
    if prompt_name not in AgentPromptName:
        raise ValueError('prompt_name must be a valid AgentPromptName constant')

    result = list_prompts(name=prompt_name, status=AgentPromptStatus.ACTIVE)

    if result.prompts:
        return

    if system_message:
        system_message = textwrap.dedent(system_message)
    if human_message:
        human_message = textwrap.dedent(human_message)
    add_prompt(
        name=prompt_name,
        owner_type=owner_type,
        status=AgentPromptStatus.ACTIVE,
        human_message=human_message,
        system_message=system_message,
        include_history=include_history,
    )
