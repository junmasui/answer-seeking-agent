import logging

import httpx

from ...lib_config import get_lib_config

logger = logging.getLogger(__name__)


def execute_presidio_check(text: str) -> dict:
    """Helper function to call the Presidio server."""
    config = get_lib_config()
    presidio_analyzer_url = str(config.presidio_analyzer_url)
    # If text is empty or only whitespace, skip the external call and return
    # an empty result immediately. This avoids unnecessary network calls
    # and prevents sending invalid payloads to the Presidio analyzer.
    if not text or not str(text).strip():
        logger.debug('empty or whitespace-only text received; returning empty result')
        return {}

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
