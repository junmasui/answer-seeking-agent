import textwrap
from functools import cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from ..status_models import PingResult, PingStatus


#
# Create chat LLM.
#
# See: https://python.langchain.com/docs/integrations/providers/openai/
#
@cache
def get_chat_llm() -> BaseChatModel:
    """
    Initializes and returns a cached instance of the ChatOpenAI model.

    This function configures the ChatOpenAI model with 'gpt-4o-mini' and
    a temperature of 0 for deterministic outputs. The instance is cached
    to avoid reinitialization on subsequent calls.

    Returns:
        BaseChatModel: A cached instance of the ChatOpenAI model.
    """
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)

    return llm


def ping_chat_llm() -> PingResult:
    """
    Pings the OpenAI model to check its operational status.

    This function sends a small completion task to the OpenAI model to verify
    not only raw connectivity but also permissions and other configurations.

    Returns:
        PingResult: An object containing the status (good/bad), a message,
                    and an optional error if the ping failed.
    """
    try:
        llm = get_chat_llm()
        message_content = """Please provide:

        Your current operational status on a scale of 0 to 10, where 10 means fully operational with no errors and 0 means completely non-functional.

        The current date and time in the following format: YYYY-MM-DD HH:MM (include your time zone).
        """
        response = llm.invoke([HumanMessage(content=textwrap.dedent(message_content))])
        if response.content:
            return PingResult(status=PingStatus.GOOD, message='OpenAI model is responsive.')
        else:
            return PingResult(status=PingStatus.BAD, message='OpenAI model responded but content is empty.')
    except Exception as e:
        return PingResult(status=PingStatus.BAD, message='Failed to ping OpenAI model.', error=str(e))
