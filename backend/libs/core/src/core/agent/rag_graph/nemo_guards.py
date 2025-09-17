import logging

import httpx

from ...lib_config import get_lib_config

logger = logging.getLogger(__name__)


def execute_nemo_guardrails_check(config_id: str, messages: list) -> dict:
    """Helper function to call the Nemo Guardrails server."""
    config = get_lib_config()
    openai_api_key = config.open_api_key
    guardrails_url = str(config.nemo_guardrails_url)

    # Validate messages early to avoid calling the external Nemo Guardrails service
    if not messages:
        # No messages supplied — return a consistent structure similar to the exception path
        return {
            'messages': [
                {
                    'role': 'assistant',
                    'content': 'No input messages provided for content checking.'
                }
            ]
        }

    # Ensure last message has meaningful content
    last_item = messages[-1]
    last_content = last_item.get('content', None) if isinstance(last_item, dict) else None
    if not last_content:
        # Last message has no content — return without calling Nemo
        return {
            'messages': [
                {
                    'role': 'assistant',
                    'content': 'Last message contains no content to check.'
                }
            ]
        }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',  # Note: Nemo server can use this for its own OpenAI calls
    }
    payload = {'config_id': config_id, 'messages': messages, 'options': {'output_vars': True}}
    try:
        with httpx.Client() as client:
            response = client.post(guardrails_url, json=payload, headers=headers, timeout=60.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.warning('Error calling guardrails API:', exc_info=e)
        return {'messages': [{'role': 'assistant', 'content': 'Error checking content.'}]}
