"""
This provides the chat LLM used by this application.
"""

import os
from functools import cache

from global_config import get_global_config

# Explicitly define the exported symbols: the exported symbols
# is part of the contract of this provider module.
__all__ = ['get_chat_llm']

llm_type = get_global_config().chat_llm_type

match llm_type:
    case 'openai':
        from .openai import get_chat_llm
    case 'huggingface':
        from .huggingface import get_chat_llm
    case 'google-genai':
        from .google_genai import get_chat_llm
    case _:
        raise ValueError(f'Unknown LLM type: {llm_type}')
