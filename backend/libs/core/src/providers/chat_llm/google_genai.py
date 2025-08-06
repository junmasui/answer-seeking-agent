from functools import cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/chat/google_generative_ai/
#


@cache
def get_chat_llm() -> BaseChatModel:
    """
    Get a cached instance of the Google Generative AI chat model.

    Returns:
        BaseChatModel: An instance of the chat model.

    """
    llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0, max_tokens=None, max_retries=2, stop=None)

    return llm


def ping_chat_llm():
    """
    Ping the Google Generative AI chat model.

    Raises:
        NotImplementedError: This function is not yet implemented.

    """
    raise NotImplementedError('Ping not implemented for Google GenAI')
