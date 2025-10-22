import textwrap
from typing import Optional

from core_public import PromptStatus, OwnerType

from ..agent.internal_models import AgentPromptName
from .prompt.add import add_prompt
from .prompt.query import list_prompts
from .prompt_version.add import add_prompt_version
from .prompt_version.query import list_prompt_versions


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

    result = list_prompts(name=prompt_name)

    if result.prompts:
        return
    
    if system_message:
        system_message = textwrap.dedent(system_message)
    if human_message:
        human_message = textwrap.dedent(human_message)

    prompt_id = add_prompt(
        name=prompt_name,
        owner_type=owner_type,
    )

    add_prompt_version(
        prompt_id=prompt_id,
        status=PromptStatus.ACTIVE,
        include_history=include_history,
        human_message=human_message,
        system_message=system_message                       
    )
