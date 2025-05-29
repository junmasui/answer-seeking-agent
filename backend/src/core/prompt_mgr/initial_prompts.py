import logging
from pathlib import Path

import yaml

from ..agent.internal_models import AgentPromptName
from ..signals import db_predefined_data_handler
from .util import add_chat_prompt

logger = logging.getLogger(__name__)


@db_predefined_data_handler
def register_initial_prompts(sender):
    """
    Register initial agent prompts from YAML configuration file.

    Loads predefined prompts from initial_prompts.yml and adds them to the database
    when the database is ready for predefined data. Only runs on non-worker processes.
    """
    if sender.is_worker:
        return

    logger.info('adding predefined prompts')

    data_path = Path(__file__).parent / 'initial_prompts.yml'
    with data_path.open('r') as yaml_file:
        prompts = yaml.safe_load(yaml_file)

    for prompt in prompts:
        prompt_name = AgentPromptName.by_name(prompt['prompt_name'])
        add_chat_prompt(
            prompt_name=prompt_name,
            system_message=prompt.get('system_message', ''),
            human_message=prompt.get('human_message', ''),
            include_history=prompt.get('include_history', False),
        )
