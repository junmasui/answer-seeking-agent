import os
from functools import cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/providers/openai/
#
@cache
def get_chat_llm() -> BaseChatModel:
    """
    """

    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)

    return llm
