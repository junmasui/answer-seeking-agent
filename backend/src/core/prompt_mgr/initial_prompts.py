import logging
import yaml
from pathlib import Path

from .util import add_chat_prompt
from ..agent.internal_models import AgentPrompt
from ..signals import db_predefined_data_handler

logger = logging.getLogger(__name__)

@db_predefined_data_handler
def register_initial_prompts(sender):
    if sender.is_worker:
        return

    logger.info('adding predefined prompts')

    data_path = Path( __file__ ).parent / 'initial_prompts.yml'
    with data_path.open('r') as yaml_file:
        prompts = yaml.safe_load(yaml_file)

    for prompt in prompts:
        prompt_name = AgentPrompt[prompt['prompt_name']]
        add_chat_prompt(
            prompt_name=prompt_name,
            system_message=prompt.get('system_message', ''),
            human_message=prompt.get('human_message', '')
        )
