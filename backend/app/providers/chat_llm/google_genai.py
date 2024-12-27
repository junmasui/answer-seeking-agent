from functools import cache
from langchain_google_genai import ChatGoogleGenerativeAI

#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/chat/google_generative_ai/
#


@cache
def get_chat_llm():
    """
    """

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash",
                       temperature=0,
                       max_tokens=None,
                       max_retries=2,
                       stop=None)

    return llm
