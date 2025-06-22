import logging

import httpx

from ..lib_config import get_lib_config

logger = logging.getLogger(__name__)

def execute_presidio_check(text: str) -> dict:
    """Helper function to call the Presidio server."""
    config = get_lib_config()
    presidio_analyzer_url = str(config.presidio_analyzer_url)

    payload = {'text': text, 'language': 'en'}
    try:
        with httpx.Client() as client:
            response = client.post(presidio_analyzer_url, json=payload, timeout=60.0)
            response.raise_for_status()
            resp = response.json()
            logger.info('presidio result: %s', resp)
            return resp
    except httpx.HTTPStatusError as e:
        logger.warning('Error calling presidio API', exc_info=e)
        return {}
