import textwrap
from typing import Optional

from core.agent.internal_models import AgentPromptName
from core.public_models import AgentPromptStatus, OwnerType

from .add import add_prompt
from .query import list_prompts


def add_chat_prompt(
    *,
    prompt_name: str,
    system_message: Optional[str] = None,
    human_message: Optional[str] = None,
    include_history: Optional[bool] = None,
):
    """Add a prompt in the database if it does not exist, using the provided defaults."""
    if prompt_name not in AgentPromptName:
        raise ValueError('prompt_name must be a valid AgentPromptName constant')

    result = list_prompts(name=prompt_name, owner_type=OwnerType.SYSTEM)

    if system_message:
        system_message = textwrap.dedent(system_message)
    if human_message:
        human_message = textwrap.dedent(human_message)

    has_matching = any(
        prompt.system_message == system_message
        and prompt.human_message == human_message
        and prompt.include_history == include_history
        for prompt in result.prompts
    )

    # If a system-controlled record already matches the YAML-defined record,
    # then do nothing.
    if has_matching:
        return

    # If a system-controlled record is the active prompt, then we will add
    # the new system-controlled record as the active prompt.
    has_active = any(prompt.status == AgentPromptStatus.ACTIVE for prompt in result.prompts)
    status = AgentPromptStatus.ACTIVE if has_active else AgentPromptStatus.DEACTIVATED

    add_prompt(
        name=prompt_name,
        status=status,
        owner_type=OwnerType.SYSTEM,
        human_message=human_message,
        system_message=system_message,
        include_history=include_history,
    )
