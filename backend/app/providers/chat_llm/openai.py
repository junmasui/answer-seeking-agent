import os
from functools import cache

from langchain_openai import ChatOpenAI

#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/providers/openai/
#
@cache
def get_chat_llm():

    llm = ChatOpenAI(model='gpt-4o-mini-2024-07-18', temperature=0)

    return llm
